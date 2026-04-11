# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""API response models for job control endpoints."""

from datetime import datetime

from pydantic import BaseModel


class JobControlOverviewResponse(BaseModel):
    """High-level broker health and queue depth summary."""

    total_queued: int
    total_unacked: int
    dlq_depth: int
    retry_depth: int
    consumers_online: int
    broker_alarms: list[str]


class QueueInfoResponse(BaseModel):
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


class WorkerInfoResponse(BaseModel):
    """Consumer (worker) information from the RabbitMQ Management API."""

    consumer_tag: str
    queue: str
    channel_details: str
    prefetch_count: int


class RecentFailedJobResponse(BaseModel):
    """A recently failed job from the database."""

    id: int
    kind: str
    course_id: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class JobFailuresResponse(BaseModel):
    """Failure summary: DLQ depth, recent failed jobs, and error buckets."""

    dlq_messages: int
    recent_failed_jobs: list[RecentFailedJobResponse]
    error_buckets: dict[str, int]
