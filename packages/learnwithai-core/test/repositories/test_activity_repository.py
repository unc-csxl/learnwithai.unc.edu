"""Tests for ActivityRepository."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from learnwithai.repositories.activity_repository import ActivityRepository
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.course import Course, Term
from learnwithai.tables.user import User
from sqlmodel import Session

TEST_PID = 555555555


def _seed_prereqs(session: Session) -> tuple[User, Course]:
    user = User(pid=TEST_PID, name="Instructor", onyen="instructor")
    session.add(user)
    session.flush()
    course = Course(course_number="COMP423", name="Foundations", term=Term.FALL, year=2026)
    session.add(course)
    session.flush()
    return user, course


def _make_activity(course: Course, user: User, **overrides: object) -> Activity:
    defaults = {
        "course_id": course.id,
        "created_by_pid": user.pid,
        "type": ActivityType.IYOW,
        "title": "Test Activity",
        "release_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "due_date": datetime(2025, 2, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return Activity(**defaults)  # type: ignore[arg-type]


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_activity(session: Session) -> None:
    user, course = _seed_prereqs(session)
    repo = ActivityRepository(session)

    result = repo.create(_make_activity(course, user))

    assert result.id is not None
    assert result.title == "Test Activity"
    assert result.type == ActivityType.IYOW
    assert result.created_at is not None


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_activity(session: Session) -> None:
    user, course = _seed_prereqs(session)
    repo = ActivityRepository(session)
    created = repo.create(_make_activity(course, user))

    result = repo.get_by_id(created.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.title == "Test Activity"


@pytest.mark.integration
def test_get_by_id_returns_none_when_not_found(session: Session) -> None:
    repo = ActivityRepository(session)
    assert repo.get_by_id(999999) is None


# --- list_by_course ---


@pytest.mark.integration
def test_list_by_course_returns_activities(session: Session) -> None:
    user, course = _seed_prereqs(session)
    repo = ActivityRepository(session)
    repo.create(_make_activity(course, user, title="A1"))
    repo.create(_make_activity(course, user, title="A2"))

    result = repo.list_by_course(course.id)  # type: ignore[arg-type]

    assert len(result) == 2


@pytest.mark.integration
def test_list_by_course_returns_empty_for_other_course(session: Session) -> None:
    user, _course = _seed_prereqs(session)
    repo = ActivityRepository(session)
    assert repo.list_by_course(999999) == []


# --- list_released_by_course ---


@pytest.mark.integration
def test_list_released_by_course_filters_by_release_date(session: Session) -> None:
    user, course = _seed_prereqs(session)
    repo = ActivityRepository(session)
    repo.create(_make_activity(course, user, title="Released", release_date=datetime(2025, 1, 1, tzinfo=timezone.utc)))
    repo.create(_make_activity(course, user, title="Future", release_date=datetime(2026, 6, 1, tzinfo=timezone.utc)))

    now = datetime(2025, 6, 1, tzinfo=timezone.utc)
    result = repo.list_released_by_course(course.id, now)  # type: ignore[arg-type]

    assert len(result) == 1
    assert result[0].title == "Released"


# --- update ---


@pytest.mark.integration
def test_update_modifies_activity(session: Session) -> None:
    user, course = _seed_prereqs(session)
    repo = ActivityRepository(session)
    activity = repo.create(_make_activity(course, user))
    activity.title = "Updated Title"

    result = repo.update(activity)

    assert result.title == "Updated Title"


# --- delete ---


@pytest.mark.integration
def test_delete_removes_activity(session: Session) -> None:
    user, course = _seed_prereqs(session)
    repo = ActivityRepository(session)
    activity = repo.create(_make_activity(course, user))
    activity_id = activity.id

    repo.delete(activity)

    assert repo.get_by_id(activity_id) is None  # type: ignore[arg-type]
