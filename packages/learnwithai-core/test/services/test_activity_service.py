# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for ActivityService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from learnwithai.errors import AuthorizationError
from learnwithai.repositories.activity_repository import ActivityRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.services.activity_service import ActivityService
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.course import Course
from learnwithai.tables.membership import MembershipType
from learnwithai.tables.user import User


def _build_service(
    activity_repo: MagicMock | None = None,
    membership_repo: MagicMock | None = None,
) -> ActivityService:
    return ActivityService(
        activity_repo=activity_repo or MagicMock(spec=ActivityRepository),
        membership_repo=membership_repo or MagicMock(spec=MembershipRepository),
    )


def _make_user(pid: int = 123456789) -> MagicMock:
    m = MagicMock(spec=User)
    m.pid = pid
    return m


def _make_course(course_id: int = 1) -> MagicMock:
    m = MagicMock(spec=Course)
    m.id = course_id
    return m


def _make_membership(type: MembershipType = MembershipType.INSTRUCTOR) -> MagicMock:
    m = MagicMock()
    m.type = type
    return m


def _make_activity(activity_id: int = 10, course_id: int = 1) -> MagicMock:
    m = MagicMock(spec=Activity)
    m.id = activity_id
    m.course_id = course_id
    m.release_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    m.type = ActivityType.IYOW
    return m


NOW = datetime(2025, 6, 1, tzinfo=timezone.utc)


# --- create_activity ---


def test_create_activity_succeeds_for_instructor() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity_repo = MagicMock(spec=ActivityRepository)
    created = _make_activity()
    activity_repo.create.return_value = created

    svc = _build_service(activity_repo, membership_repo)
    result = svc.create_activity(
        _make_user(),
        _make_course(),
        ActivityType.IYOW,
        "Title",
        datetime(2025, 1, 1, tzinfo=timezone.utc),
        datetime(2025, 2, 1, tzinfo=timezone.utc),
    )

    assert result is created
    activity_repo.create.assert_called_once()


def test_create_activity_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.create_activity(
            _make_user(),
            _make_course(),
            ActivityType.IYOW,
            "Title",
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 2, 1, tzinfo=timezone.utc),
        )


def test_create_activity_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.create_activity(
            _make_user(),
            _make_course(),
            ActivityType.IYOW,
            "Title",
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 2, 1, tzinfo=timezone.utc),
        )


# --- list_activities ---


def test_list_activities_instructor_sees_all() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.list_by_course.return_value = [_make_activity()]

    svc = _build_service(activity_repo, membership_repo)
    result = svc.list_activities(_make_user(), _make_course(), NOW)

    assert len(result) == 1
    activity_repo.list_by_course.assert_called_once()


def test_list_activities_ta_sees_all() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.TA)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.list_by_course.return_value = []

    svc = _build_service(activity_repo, membership_repo)
    svc.list_activities(_make_user(), _make_course(), NOW)

    activity_repo.list_by_course.assert_called_once()


def test_list_activities_student_sees_released_only() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.list_released_by_course.return_value = []

    svc = _build_service(activity_repo, membership_repo)
    svc.list_activities(_make_user(), _make_course(), NOW)

    activity_repo.list_released_by_course.assert_called_once()


def test_list_activities_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.list_activities(_make_user(), _make_course(), NOW)


# --- get_activity ---


def test_get_activity_returns_for_instructor() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity = _make_activity()
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.get_by_id.return_value = activity

    svc = _build_service(activity_repo, membership_repo)
    result = svc.get_activity(_make_user(), _make_course(), 10, NOW)

    assert result is activity


def test_get_activity_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.get_activity(_make_user(), _make_course(), 10, NOW)


def test_get_activity_raises_when_not_found() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.get_by_id.return_value = None

    svc = _build_service(activity_repo, membership_repo)

    with pytest.raises(ValueError, match="not found in course"):
        svc.get_activity(_make_user(), _make_course(), 999, NOW)


def test_get_activity_raises_when_wrong_course() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity = _make_activity(course_id=99)  # Different course
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.get_by_id.return_value = activity

    svc = _build_service(activity_repo, membership_repo)

    with pytest.raises(ValueError, match="not found in course"):
        svc.get_activity(_make_user(), _make_course(course_id=1), 10, NOW)


def test_get_activity_student_cannot_access_unreleased() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)
    activity = _make_activity()
    activity.release_date = datetime(2030, 1, 1, tzinfo=timezone.utc)  # Far future
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.get_by_id.return_value = activity

    svc = _build_service(activity_repo, membership_repo)

    with pytest.raises(AuthorizationError, match="not yet released"):
        svc.get_activity(_make_user(), _make_course(), 10, NOW)


def test_get_activity_student_can_access_released() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)
    activity = _make_activity()
    activity.release_date = datetime(2020, 1, 1, tzinfo=timezone.utc)  # Past
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.get_by_id.return_value = activity

    svc = _build_service(activity_repo, membership_repo)
    result = svc.get_activity(_make_user(), _make_course(), 10, NOW)

    assert result is activity


# --- update_activity ---


def test_update_activity_succeeds_for_staff() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity = _make_activity()
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.update.return_value = activity

    svc = _build_service(activity_repo, membership_repo)
    result = svc.update_activity(
        _make_user(),
        _make_course(),
        activity,
        "New Title",
        datetime(2025, 1, 1, tzinfo=timezone.utc),
        datetime(2025, 3, 1, tzinfo=timezone.utc),
    )

    assert result is activity
    activity_repo.update.assert_called_once()


def test_update_activity_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.update_activity(
            _make_user(),
            _make_course(),
            _make_activity(),
            "Title",
            datetime(2025, 1, 1, tzinfo=timezone.utc),
            datetime(2025, 2, 1, tzinfo=timezone.utc),
        )


# --- delete_activity ---


def test_delete_activity_succeeds_for_instructor() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity = _make_activity()

    svc = _build_service(activity_repo, membership_repo)
    svc.delete_activity(_make_user(), _make_course(), activity)

    activity_repo.delete.assert_called_once_with(activity)


def test_delete_activity_raises_for_ta() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.TA)

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError, match="Only instructors"):
        svc.delete_activity(_make_user(), _make_course(), _make_activity())


def test_delete_activity_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _build_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.delete_activity(_make_user(), _make_course(), _make_activity())
