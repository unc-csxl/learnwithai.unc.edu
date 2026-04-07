# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for IyowActivityService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from learnwithai.activities.iyow.repository import IyowActivityRepository
from learnwithai.activities.iyow.service import IyowActivityService
from learnwithai.activities.iyow.tables import IyowActivity
from learnwithai.errors import AuthorizationError
from learnwithai.repositories.activity_repository import ActivityRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.course import Course
from learnwithai.tables.membership import MembershipType
from learnwithai.tables.user import User


def _make_service(
    activity_repo: MagicMock | None = None,
    iyow_activity_repo: MagicMock | None = None,
    membership_repo: MagicMock | None = None,
) -> IyowActivityService:
    return IyowActivityService(
        activity_repo=activity_repo or MagicMock(spec=ActivityRepository),
        iyow_activity_repo=iyow_activity_repo or MagicMock(spec=IyowActivityRepository),
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
    m.type = ActivityType.IYOW
    return m


def _make_iyow_detail(activity_id: int = 10) -> MagicMock:
    m = MagicMock(spec=IyowActivity)
    m.activity_id = activity_id
    m.prompt = "Explain X"
    m.rubric = "Good answer mentions Y"
    return m


RELEASE = datetime(2025, 1, 1, tzinfo=timezone.utc)
DUE = datetime(2025, 2, 1, tzinfo=timezone.utc)
LATE = datetime(2025, 2, 15, tzinfo=timezone.utc)


# ---- create_iyow_activity ----


def test_create_iyow_activity_succeeds_for_instructor() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity_repo = MagicMock(spec=ActivityRepository)
    created_activity = _make_activity()
    activity_repo.create.return_value = created_activity
    iyow_repo = MagicMock(spec=IyowActivityRepository)
    created_detail = _make_iyow_detail()
    iyow_repo.create.return_value = created_detail

    svc = _make_service(activity_repo, iyow_repo, membership_repo)
    activity, detail = svc.create_iyow_activity(
        _make_user(), _make_course(), "Title", "Prompt", "Rubric", RELEASE, DUE, LATE
    )

    assert activity is created_activity
    assert detail is created_detail
    activity_repo.create.assert_called_once()
    iyow_repo.create.assert_called_once()


def test_create_iyow_activity_succeeds_for_ta() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.TA)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity_repo.create.return_value = _make_activity()
    iyow_repo = MagicMock(spec=IyowActivityRepository)
    iyow_repo.create.return_value = _make_iyow_detail()

    svc = _make_service(activity_repo, iyow_repo, membership_repo)
    svc.create_iyow_activity(_make_user(), _make_course(), "T", "P", "R", RELEASE, DUE)


def test_create_iyow_activity_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.create_iyow_activity(_make_user(), _make_course(), "T", "P", "R", RELEASE, DUE)


def test_create_iyow_activity_raises_for_non_member() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = None

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.create_iyow_activity(_make_user(), _make_course(), "T", "P", "R", RELEASE, DUE)


# ---- get_iyow_detail ----


def test_get_iyow_detail_returns_detail() -> None:
    iyow_repo = MagicMock(spec=IyowActivityRepository)
    detail = _make_iyow_detail()
    iyow_repo.get_by_activity_id.return_value = detail

    svc = _make_service(iyow_activity_repo=iyow_repo)
    result = svc.get_iyow_detail(10)

    assert result is detail


def test_get_iyow_detail_raises_when_not_found() -> None:
    iyow_repo = MagicMock(spec=IyowActivityRepository)
    iyow_repo.get_by_activity_id.return_value = None

    svc = _make_service(iyow_activity_repo=iyow_repo)

    with pytest.raises(ValueError, match="IYOW detail not found"):
        svc.get_iyow_detail(999)


# ---- update_iyow_activity ----


def test_update_iyow_activity_succeeds() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.INSTRUCTOR)
    activity_repo = MagicMock(spec=ActivityRepository)
    activity = _make_activity()
    activity_repo.update.return_value = activity
    iyow_repo = MagicMock(spec=IyowActivityRepository)
    detail = _make_iyow_detail()
    iyow_repo.get_by_activity_id.return_value = detail
    iyow_repo.update.return_value = detail

    svc = _make_service(activity_repo, iyow_repo, membership_repo)
    result_act, result_det = svc.update_iyow_activity(
        _make_user(), _make_course(), activity, "New Title", "New Prompt", "New Rubric", RELEASE, DUE, LATE
    )

    activity_repo.update.assert_called_once()
    iyow_repo.update.assert_called_once()


def test_update_iyow_activity_raises_for_student() -> None:
    membership_repo = MagicMock(spec=MembershipRepository)
    membership_repo.get_by_user_and_course.return_value = _make_membership(MembershipType.STUDENT)

    svc = _make_service(membership_repo=membership_repo)

    with pytest.raises(AuthorizationError):
        svc.update_iyow_activity(_make_user(), _make_course(), _make_activity(), "T", "P", "R", RELEASE, DUE)
