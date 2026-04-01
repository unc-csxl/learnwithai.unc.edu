"""Tests for IyowActivityRepository and IyowSubmissionRepository."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from learnwithai.activities.iyow.repository import (
    IyowActivityRepository,
    IyowSubmissionRepository,
)
from learnwithai.activities.iyow.tables import IyowActivity, IyowSubmission
from learnwithai.tables.activity import Activity, ActivityType
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tables.course import Course, Term
from learnwithai.tables.submission import Submission
from learnwithai.tables.user import User
from sqlmodel import Session

STUDENT_PID = 888888888
INSTRUCTOR_PID = 999999999


def _seed_prereqs(session: Session) -> tuple[User, Course, Activity]:
    """Create user, course, and base activity."""
    instructor = User(pid=INSTRUCTOR_PID, name="Instructor", onyen="instructor")
    student = User(pid=STUDENT_PID, name="Student", onyen="student")
    session.add(instructor)
    session.add(student)
    session.flush()

    course = Course(course_number="COMP423", name="Foundations", term=Term.FALL, year=2026)
    session.add(course)
    session.flush()
    assert course.id is not None

    activity = Activity(
        course_id=course.id,
        created_by_pid=instructor.pid,
        type=ActivityType.IYOW,
        title="IYOW Test",
        release_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        due_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    session.add(activity)
    session.flush()
    assert activity.id is not None

    return student, course, activity


# ---- IyowActivityRepository ----


@pytest.mark.integration
def test_iyow_activity_create_and_get(session: Session) -> None:
    _student, _course, activity = _seed_prereqs(session)
    repo = IyowActivityRepository(session)

    detail = repo.create(IyowActivity(activity_id=activity.id, prompt="Explain X", rubric="Be clear"))  # type: ignore[arg-type]

    assert detail.id is not None
    assert detail.prompt == "Explain X"

    fetched = repo.get_by_activity_id(activity.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.prompt == "Explain X"


@pytest.mark.integration
def test_iyow_activity_get_returns_none(session: Session) -> None:
    repo = IyowActivityRepository(session)
    assert repo.get_by_activity_id(999999) is None


@pytest.mark.integration
def test_iyow_activity_update(session: Session) -> None:
    _student, _course, activity = _seed_prereqs(session)
    repo = IyowActivityRepository(session)
    detail = repo.create(IyowActivity(activity_id=activity.id, prompt="Old", rubric="Old"))  # type: ignore[arg-type]

    detail.prompt = "New"
    result = repo.update(detail)

    assert result.prompt == "New"


# ---- IyowSubmissionRepository ----


def _seed_submission(session: Session) -> tuple[Activity, Submission, AsyncJob]:
    """Create activity + base submission + async job for IYOW submission tests."""
    _student, course, activity = _seed_prereqs(session)

    base_sub = Submission(
        activity_id=activity.id,  # type: ignore[arg-type]
        student_pid=STUDENT_PID,
        is_active=True,
        submitted_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    session.add(base_sub)
    session.flush()
    assert base_sub.id is not None

    async_job = AsyncJob(
        course_id=course.id,  # type: ignore[arg-type]
        created_by_pid=STUDENT_PID,
        kind="iyow_feedback",
        status=AsyncJobStatus.PENDING,
        input_data={},
    )
    session.add(async_job)
    session.flush()
    assert async_job.id is not None

    return activity, base_sub, async_job


@pytest.mark.integration
def test_iyow_submission_create_and_get(session: Session) -> None:
    _activity, base_sub, async_job = _seed_submission(session)
    repo = IyowSubmissionRepository(session)

    detail = repo.create(
        IyowSubmission(
            submission_id=base_sub.id,  # type: ignore[arg-type]
            response_text="My explanation",
            async_job_id=async_job.id,  # type: ignore[arg-type]
        )
    )

    assert detail.id is not None

    fetched = repo.get_by_submission_id(base_sub.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.response_text == "My explanation"


@pytest.mark.integration
def test_iyow_submission_get_by_submission_id_returns_none(session: Session) -> None:
    repo = IyowSubmissionRepository(session)
    assert repo.get_by_submission_id(999999) is None


@pytest.mark.integration
def test_iyow_submission_get_by_async_job_id(session: Session) -> None:
    _activity, base_sub, async_job = _seed_submission(session)
    repo = IyowSubmissionRepository(session)
    repo.create(
        IyowSubmission(
            submission_id=base_sub.id,  # type: ignore[arg-type]
            response_text="Answer",
            async_job_id=async_job.id,  # type: ignore[arg-type]
        )
    )

    fetched = repo.get_by_async_job_id(async_job.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.response_text == "Answer"


@pytest.mark.integration
def test_iyow_submission_get_by_async_job_id_returns_none(session: Session) -> None:
    repo = IyowSubmissionRepository(session)
    assert repo.get_by_async_job_id(999999) is None


@pytest.mark.integration
def test_iyow_submission_update(session: Session) -> None:
    _activity, base_sub, async_job = _seed_submission(session)
    repo = IyowSubmissionRepository(session)
    detail = repo.create(
        IyowSubmission(
            submission_id=base_sub.id,  # type: ignore[arg-type]
            response_text="Original",
            async_job_id=async_job.id,  # type: ignore[arg-type]
        )
    )

    detail.feedback = "Great job!"
    result = repo.update(detail)

    assert result.feedback == "Great job!"
