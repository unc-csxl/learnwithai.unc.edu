# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Business logic for job control and RabbitMQ monitoring."""

from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Session, col, func, select

from ..rabbitmq_management import RabbitMQManagementClient
from ..services.operator_service import OperatorService
from ..tables.async_job import AsyncJob, AsyncJobStatus
from ..tables.user import User


class JobControlOverview(BaseModel):
    """High-level broker health and queue depth summary."""

    total_queued: int
    total_unacked: int
    dlq_depth: int
    retry_depth: int
    consumers_online: int
    broker_alarms: list[str]


class QueueInfo(BaseModel):
    """Per-queue statistics from the RabbitMQ Management API."""

    name: str
    ready: int
    unacked: int
    consumers: int
    ack_rate: float
    is_dlq: bool
    is_retry: bool
    message_ttl_ms: int | None = None
    dead_letter_exchange: str | None = None
    dead_letter_routing_key: str | None = None


class WorkerInfo(BaseModel):
    """Consumer (worker) information from the RabbitMQ Management API."""

    consumer_tag: str
    queue: str
    channel_details: str
    prefetch_count: int


class RecentFailedJob(BaseModel):
    """A recently failed job from the database."""

    id: int
    kind: str
    course_id: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class JobFailures(BaseModel):
    """Failure summary: DLQ depth, recent failed jobs, and error buckets."""

    dlq_messages: int
    recent_failed_jobs: list[RecentFailedJob]
    error_buckets: dict[str, int]


class JobControlService:
    """Provides job control and monitoring for operators.

    Combines RabbitMQ Management API data with application database
    queries to give operators visibility into broker health, queue
    depths, worker status, and recent job failures.
    """

    def __init__(
        self,
        session: Session,
        operator_service: OperatorService,
        rabbitmq_client: RabbitMQManagementClient,
    ) -> None:
        """Initializes the job control service.

        Args:
            session: Database session for failure queries.
            operator_service: Service for permission enforcement.
            rabbitmq_client: Client for RabbitMQ Management API.
        """
        self._session = session
        self._operator_service = operator_service
        self._rabbitmq_client = rabbitmq_client

    # -- Public API --

    def get_overview(self, subject: User) -> JobControlOverview:
        """Returns a high-level overview of broker health and queue depths.

        Requires ``VIEW_JOBS`` permission.

        Args:
            subject: Authenticated operator.

        Returns:
            Broker health summary.
        """
        self._require_view_jobs(subject)
        queues = self._rabbitmq_client.get_queues()
        overview = self._rabbitmq_client.get_overview()

        total_queued = 0
        total_unacked = 0
        dlq_depth = 0
        retry_depth = 0
        consumers_online = 0

        for q in queues:
            ready = q.get("messages_ready", 0)
            unacked = q.get("messages_unacknowledged", 0)
            name = q.get("name", "")
            total_queued += ready
            total_unacked += unacked
            consumers_online += q.get("consumers", 0)

            if name.endswith(".DQ"):
                dlq_depth += ready
            elif name.endswith(".XQ"):
                retry_depth += ready

        alarms: list[str] = []
        for alarm in overview.get("alarms", []):
            resource = alarm.get("resource", "unknown")
            alarms.append(str(resource))

        return JobControlOverview(
            total_queued=total_queued,
            total_unacked=total_unacked,
            dlq_depth=dlq_depth,
            retry_depth=retry_depth,
            consumers_online=consumers_online,
            broker_alarms=alarms,
        )

    def get_queues(self, subject: User) -> list[QueueInfo]:
        """Returns per-queue statistics.

        Requires ``VIEW_JOBS`` permission.

        Args:
            subject: Authenticated operator.

        Returns:
            List of queue statistics.
        """
        self._require_view_jobs(subject)
        queues = self._rabbitmq_client.get_queues()

        result: list[QueueInfo] = []
        for q in queues:
            name = q.get("name", "")
            details = q.get("message_stats", {})
            arguments = q.get("arguments", {})
            ack_rate = 0.0
            if details:
                ack_details = details.get("ack_details", {})
                ack_rate = ack_details.get("rate", 0.0)
            if not isinstance(arguments, dict):
                arguments = {}

            result.append(
                QueueInfo(
                    name=name,
                    ready=q.get("messages_ready", 0),
                    unacked=q.get("messages_unacknowledged", 0),
                    consumers=q.get("consumers", 0),
                    ack_rate=ack_rate,
                    is_dlq=name.endswith(".DQ"),
                    is_retry=name.endswith(".XQ"),
                    message_ttl_ms=self._coerce_optional_int(arguments.get("x-message-ttl")),
                    dead_letter_exchange=self._coerce_optional_str(arguments.get("x-dead-letter-exchange")),
                    dead_letter_routing_key=self._coerce_optional_str(arguments.get("x-dead-letter-routing-key")),
                )
            )

        return result

    def get_workers(self, subject: User) -> list[WorkerInfo]:
        """Returns active consumer (worker) information.

        Requires ``VIEW_JOBS`` permission.

        Args:
            subject: Authenticated operator.

        Returns:
            List of active consumers.
        """
        self._require_view_jobs(subject)
        consumers = self._rabbitmq_client.get_consumers()

        result: list[WorkerInfo] = []
        for c in consumers:
            channel = c.get("channel_details", {})
            channel_str = channel.get("name", "") if isinstance(channel, dict) else str(channel)

            result.append(
                WorkerInfo(
                    consumer_tag=c.get("consumer_tag", ""),
                    queue=c.get("queue", {}).get("name", "") if isinstance(c.get("queue"), dict) else "",
                    channel_details=channel_str,
                    prefetch_count=c.get("prefetch_count", 0),
                )
            )

        return result

    def get_failures(self, subject: User) -> JobFailures:
        """Returns failure summary combining DLQ depth and DB failed jobs.

        Requires ``VIEW_JOBS`` permission.

        Args:
            subject: Authenticated operator.

        Returns:
            Failure summary with DLQ depth, recent failures, and error buckets.
        """
        self._require_view_jobs(subject)

        # DLQ depth from RabbitMQ
        queues = self._rabbitmq_client.get_queues()
        dlq_messages = sum(q.get("messages_ready", 0) for q in queues if q.get("name", "").endswith(".DQ"))

        # Recent failed jobs from DB
        stmt = (
            select(AsyncJob)
            .where(col(AsyncJob.status) == AsyncJobStatus.FAILED)
            .order_by(col(AsyncJob.created_at).desc())
            .limit(50)
        )
        failed_jobs = list(self._session.exec(stmt).all())

        recent = [
            RecentFailedJob(
                id=job.id,  # type: ignore[arg-type]
                kind=job.kind,
                course_id=job.course_id,
                error_message=job.error_message,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
            for job in failed_jobs
        ]

        # Error buckets by kind
        bucket_stmt = (
            select(AsyncJob.kind, func.count())
            .where(col(AsyncJob.status) == AsyncJobStatus.FAILED)
            .group_by(AsyncJob.kind)
        )
        error_buckets: dict[str, int] = {}
        for kind, count in self._session.exec(bucket_stmt).all():
            error_buckets[kind] = int(count)

        return JobFailures(
            dlq_messages=dlq_messages,
            recent_failed_jobs=recent,
            error_buckets=error_buckets,
        )

    def purge_queue(self, subject: User, queue_name: str) -> None:
        """Purges all messages from the specified queue.

        Requires ADMIN role (``MANAGE_OPERATORS`` permission).

        Args:
            subject: Authenticated operator.
            queue_name: Name of the queue to purge.
        """
        from ..tables.operator import OperatorPermission

        self._operator_service.require_permission(subject, OperatorPermission.MANAGE_OPERATORS)
        self._rabbitmq_client.purge_queue(queue_name)

    # -- Private helpers --

    def _require_view_jobs(self, subject: User) -> None:
        """Enforces VIEW_JOBS permission."""
        from ..tables.operator import OperatorPermission

        self._operator_service.require_permission(subject, OperatorPermission.VIEW_JOBS)

    def _coerce_optional_int(self, value: object) -> int | None:
        """Returns an int when the management API argument is numeric."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def _coerce_optional_str(self, value: object) -> str | None:
        """Returns a string when the management API argument is textual."""
        return value if isinstance(value, str) else None
