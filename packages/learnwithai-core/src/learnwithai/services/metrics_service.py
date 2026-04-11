# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Business logic for platform usage metrics."""

from datetime import datetime, timezone

from pydantic import BaseModel
from sqlmodel import Session, col, func, select

from ..services.operator_service import OperatorService
from ..tables.async_job import AsyncJob
from ..tables.membership import Membership, MembershipState
from ..tables.submission import Submission
from ..tables.user import User


class UsageMetrics(BaseModel):
    """Monthly usage statistics for the platform."""

    month_label: str
    active_users: int
    active_courses: int
    submissions: int
    jobs_run: int


class MetricsService:
    """Provides platform-wide usage metrics for operators."""

    def __init__(self, session: Session, operator_service: OperatorService):
        """Initializes the metrics service.

        Args:
            session: Database session for aggregate queries.
            operator_service: Service for permission enforcement.
        """
        self._session = session
        self._operator_service = operator_service

    # -- Public API --

    def get_usage_metrics(self, subject: User) -> UsageMetrics:
        """Returns monthly usage metrics for the platform.

        Requires ``VIEW_METRICS`` permission.

        Args:
            subject: Authenticated operator requesting metrics.

        Returns:
            Usage metrics for the current month.

        Raises:
            AuthorizationError: If the subject lacks VIEW_METRICS permission.
        """
        from ..tables.operator import OperatorPermission

        self._operator_service.require_permission(subject, OperatorPermission.VIEW_METRICS)

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_label = now.strftime("%B %Y")

        return UsageMetrics(
            month_label=month_label,
            active_users=self._count_active_users(month_start),
            active_courses=self._count_active_courses(month_start),
            submissions=self._count_submissions(month_start),
            jobs_run=self._count_jobs(month_start),
        )

    # -- Private helpers --

    def _count_active_users(self, since: datetime) -> int:
        """Counts users who have been active since the given date."""
        stmt = select(func.count()).select_from(User).where(col(User.updated_at) >= since)
        return int(self._session.exec(stmt).one())

    def _count_active_courses(self, since: datetime) -> int:
        """Counts courses with at least one enrolled membership updated this month."""
        subquery = (
            select(Membership.course_id)
            .where(
                col(Membership.state) == MembershipState.ENROLLED,
                col(Membership.updated_at) >= since,
            )
            .distinct()
            .subquery()
        )
        stmt = select(func.count()).select_from(subquery)
        return int(self._session.exec(stmt).one())

    def _count_submissions(self, since: datetime) -> int:
        """Counts submissions made since the given date."""
        stmt = select(func.count()).select_from(Submission).where(col(Submission.submitted_at) >= since)
        return int(self._session.exec(stmt).one())

    def _count_jobs(self, since: datetime) -> int:
        """Counts async jobs created since the given date."""
        stmt = select(func.count()).select_from(AsyncJob).where(col(AsyncJob.created_at) >= since)
        return int(self._session.exec(stmt).one())
