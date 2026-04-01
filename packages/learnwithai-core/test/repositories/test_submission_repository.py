"""Tests for SubmissionRepository."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from learnwithai.repositories.submission_repository import SubmissionRepository
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.course import Course, Term
from learnwithai.tables.submission import Submission
from learnwithai.tables.user import User
from sqlmodel import Session

STUDENT_PID = 666666666
INSTRUCTOR_PID = 777777777


def _seed_prereqs(session: Session) -> tuple[User, Course, Activity]:
    user = User(pid=INSTRUCTOR_PID, name="Instructor", onyen="instructor")
    student = User(pid=STUDENT_PID, name="Student", onyen="student")
    session.add(user)
    session.add(student)
    session.flush()
    course = Course(course_number="COMP423", name="Foundations", term=Term.FALL, year=2026)
    session.add(course)
    session.flush()
    assert course.id is not None
    activity = Activity(
        course_id=course.id,
        created_by_pid=user.pid,
        type=ActivityType.IYOW,
        title="Test",
        release_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        due_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    session.add(activity)
    session.flush()
    return student, course, activity


def _make_submission(activity: Activity, student_pid: int = STUDENT_PID, **overrides: object) -> Submission:
    defaults = {
        "activity_id": activity.id,
        "student_pid": student_pid,
        "is_active": True,
        "submitted_at": datetime(2025, 1, 15, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return Submission(**defaults)  # type: ignore[arg-type]


# --- create ---


@pytest.mark.integration
def test_create_persists_submission(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)

    result = repo.create(_make_submission(activity))

    assert result.id is not None
    assert result.is_active is True


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_submission(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    created = repo.create(_make_submission(activity))

    result = repo.get_by_id(created.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.student_pid == STUDENT_PID


@pytest.mark.integration
def test_get_by_id_returns_none(session: Session) -> None:
    repo = SubmissionRepository(session)
    assert repo.get_by_id(999999) is None


# --- get_active_for_student ---


@pytest.mark.integration
def test_get_active_for_student_returns_active(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    repo.create(_make_submission(activity))

    result = repo.get_active_for_student(activity.id, STUDENT_PID)  # type: ignore[arg-type]

    assert result is not None
    assert result.is_active is True


@pytest.mark.integration
def test_get_active_for_student_returns_none_when_inactive(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    repo.create(_make_submission(activity, is_active=False))

    result = repo.get_active_for_student(activity.id, STUDENT_PID)  # type: ignore[arg-type]

    assert result is None


# --- list_by_activity ---


@pytest.mark.integration
def test_list_by_activity_returns_active_only(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    repo.create(_make_submission(activity, is_active=True))
    repo.create(_make_submission(activity, is_active=False, submitted_at=datetime(2025, 1, 14, tzinfo=timezone.utc)))

    result = repo.list_by_activity(activity.id)  # type: ignore[arg-type]

    assert len(result) == 1
    assert result[0].is_active is True


# --- list_by_student_and_activity ---


@pytest.mark.integration
def test_list_by_student_and_activity_returns_all(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    repo.create(_make_submission(activity, is_active=True))
    repo.create(_make_submission(activity, is_active=False, submitted_at=datetime(2025, 1, 14, tzinfo=timezone.utc)))

    result = repo.list_by_student_and_activity(activity.id, STUDENT_PID)  # type: ignore[arg-type]

    assert len(result) == 2


# --- deactivate_active ---


@pytest.mark.integration
def test_deactivate_active_sets_is_active_false(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    repo.create(_make_submission(activity))

    repo.deactivate_active(activity.id, STUDENT_PID)  # type: ignore[arg-type]

    result = repo.get_active_for_student(activity.id, STUDENT_PID)  # type: ignore[arg-type]
    assert result is None


# --- update ---


@pytest.mark.integration
def test_update_modifies_submission(session: Session) -> None:
    student, course, activity = _seed_prereqs(session)
    repo = SubmissionRepository(session)
    sub = repo.create(_make_submission(activity))
    sub.is_active = False

    result = repo.update(sub)

    assert result.is_active is False
