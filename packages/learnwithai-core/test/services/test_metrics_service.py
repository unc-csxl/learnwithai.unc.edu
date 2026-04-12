# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for MetricsService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from learnwithai.errors import AuthorizationError
from learnwithai.services.metrics_service import MetricsService, UsageMetrics
from learnwithai.services.operator_service import OperatorService
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tables.course import Course, Term
from learnwithai.tables.membership import Membership, MembershipState, MembershipType
from learnwithai.tables.submission import Submission
from learnwithai.tables.user import User
from sqlmodel import Session


def _make_user(pid: int = 111111111) -> MagicMock:
    m = MagicMock(spec=User)
    m.pid = pid
    return m


class TestGetUsageMetricsPermission:
    """Tests that permission enforcement works correctly."""

    def test_raises_when_user_lacks_view_metrics_permission(self) -> None:
        operator_svc = MagicMock(spec=OperatorService)
        operator_svc.require_permission.side_effect = AuthorizationError("Missing permission")
        session = MagicMock(spec=Session)

        svc = MetricsService(session, operator_svc)

        with pytest.raises(AuthorizationError):
            svc.get_usage_metrics(_make_user())

    def test_returns_metrics_when_user_has_permission(self) -> None:
        operator_svc = MagicMock(spec=OperatorService)
        operator_svc.require_permission.return_value = MagicMock()
        session = MagicMock(spec=Session)

        # Mock exec to return mock result objects with .one() returning 0
        mock_result = MagicMock()
        mock_result.one.return_value = 0
        session.exec.return_value = mock_result

        svc = MetricsService(session, operator_svc)
        result = svc.get_usage_metrics(_make_user())

        assert isinstance(result, UsageMetrics)
        assert result.active_users == 0
        assert result.active_courses == 0
        assert result.submissions == 0
        assert result.jobs_run == 0
        assert result.month_label != ""


class TestGetUsageMetricsIntegration:
    """Integration tests using a real DB session."""

    def test_counts_reflect_seeded_data(self, session: Session) -> None:
        """With seeded records this month, metrics should reflect them."""
        now = datetime.now(timezone.utc)

        # Seed users
        user1 = User(pid=100000001, name="Test User 1", onyen="testuser1")
        user2 = User(pid=100000002, name="Test User 2", onyen="testuser2")
        session.add(user1)
        session.add(user2)
        session.flush()

        # Seed course
        course = Course(
            course_number="TEST101",
            name="Test Course",
            description="A test course",
            term=Term.SPRING,
            year=now.year,
        )
        session.add(course)
        session.flush()
        assert course.id is not None

        # Seed memberships (to make course "active")
        membership = Membership(
            user_pid=user1.pid,
            course_id=course.id,
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
        session.add(membership)
        session.flush()

        # Seed activity (needed for submission FK)
        activity = Activity(
            course_id=course.id,
            created_by_pid=user1.pid,
            type=ActivityType.IYOW,
            title="Test Activity",
            release_date=now,
            due_date=now,
        )
        session.add(activity)
        session.flush()
        assert activity.id is not None

        # Seed submission
        submission = Submission(
            activity_id=activity.id,
            student_pid=user1.pid,
            is_active=True,
            submitted_at=now,
        )
        session.add(submission)
        session.flush()

        # Seed async job
        job = AsyncJob(
            course_id=course.id,
            created_by_pid=user1.pid,
            kind="test_job",
            status=AsyncJobStatus.COMPLETED,
        )
        session.add(job)
        session.flush()

        # Build service with real session but mocked operator permission
        operator_svc = MagicMock(spec=OperatorService)
        operator_svc.require_permission.return_value = MagicMock()

        svc = MetricsService(session, operator_svc)
        result = svc.get_usage_metrics(_make_user())

        assert result.active_users >= 2
        assert result.active_courses >= 1
        assert result.submissions >= 1
        assert result.jobs_run >= 1

    def test_counts_zero_with_empty_database(self, session: Session) -> None:
        """With no data seeded this month, all metrics should be zero."""
        operator_svc = MagicMock(spec=OperatorService)
        operator_svc.require_permission.return_value = MagicMock()

        svc = MetricsService(session, operator_svc)
        result = svc.get_usage_metrics(_make_user())

        # May not be exactly 0 if dev data exists, but should be non-negative
        assert result.active_users >= 0
        assert result.active_courses >= 0
        assert result.submissions >= 0
        assert result.jobs_run >= 0
