"""Integration tests for async job repository."""

from __future__ import annotations

import pytest
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tables.course import Course, Term
from learnwithai.tables.user import User
from sqlmodel import Session

TEST_PIDS = (123456789, 111, 222, 333)


def _seed_users(session: Session) -> None:
    for pid in TEST_PIDS:
        session.add(User(pid=pid, name=f"User {pid}", onyen=f"user{pid}"))
    session.flush()


def _seed_course(session: Session) -> Course:
    course = Course(course_number="COMP101", name="Intro to CS", term=Term.FALL, year=2026)
    session.add(course)
    session.flush()
    return course


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_job(session: Session) -> None:
    # Arrange
    _seed_users(session)
    course = _seed_course(session)
    repo = AsyncJobRepository(session)
    assert course.id is not None
    job = AsyncJob(
        course_id=course.id,
        created_by_pid=123456789,
        kind="roster_upload",
        input_data={"csv_text": "header\nrow"},
    )

    # Act
    result = repo.create(job)

    # Assert
    assert result.id is not None
    assert result.course_id == course.id
    assert result.created_by_pid == 123456789
    assert result.kind == "roster_upload"
    assert result.status == AsyncJobStatus.PENDING
    assert result.input_data == {"csv_text": "header\nrow"}
    assert result.output_data is None
    assert result.error_message is None
    assert result.created_at is not None
    assert result.completed_at is None


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_job(session: Session) -> None:
    # Arrange
    _seed_users(session)
    course = _seed_course(session)
    repo = AsyncJobRepository(session)
    assert course.id is not None
    created = repo.create(
        AsyncJob(
            course_id=course.id,
            created_by_pid=123456789,
            kind="roster_upload",
            input_data={"csv_text": "data"},
        )
    )

    # Act
    result = repo.get_by_id(created.id)  # type: ignore[arg-type]

    # Assert
    assert result is not None
    assert result.id == created.id
    assert result.kind == "roster_upload"


@pytest.mark.integration
def test_get_by_id_returns_none_for_missing(session: Session) -> None:
    # Arrange
    repo = AsyncJobRepository(session)

    # Act
    result = repo.get_by_id(99999)

    # Assert
    assert result is None


# --- list_by_course_and_kind ---


@pytest.mark.integration
def test_list_by_course_and_kind_returns_matching_jobs(
    session: Session,
) -> None:
    # Arrange
    _seed_users(session)
    course = _seed_course(session)
    repo = AsyncJobRepository(session)
    assert course.id is not None
    repo.create(
        AsyncJob(
            course_id=course.id,
            created_by_pid=111,
            kind="roster_upload",
            input_data={"csv_text": "first"},
        )
    )
    repo.create(
        AsyncJob(
            course_id=course.id,
            created_by_pid=222,
            kind="roster_upload",
            input_data={"csv_text": "second"},
        )
    )
    repo.create(
        AsyncJob(
            course_id=course.id,
            created_by_pid=333,
            kind="joke_generation",
            input_data={"prompt": "tell me a joke"},
        )
    )

    # Act
    results = repo.list_by_course_and_kind(course.id, "roster_upload")

    # Assert
    assert len(results) == 2
    kinds = {r.kind for r in results}
    assert kinds == {"roster_upload"}


@pytest.mark.integration
def test_list_by_course_and_kind_returns_empty_for_no_matches(
    session: Session,
) -> None:
    # Arrange
    course = _seed_course(session)
    repo = AsyncJobRepository(session)
    assert course.id is not None

    # Act
    results = repo.list_by_course_and_kind(course.id, "roster_upload")

    # Assert
    assert results == []


# --- update ---


@pytest.mark.integration
def test_update_modifies_job_status(session: Session) -> None:
    # Arrange
    _seed_users(session)
    course = _seed_course(session)
    repo = AsyncJobRepository(session)
    assert course.id is not None
    job = repo.create(
        AsyncJob(
            course_id=course.id,
            created_by_pid=123456789,
            kind="roster_upload",
            input_data={"csv_text": "data"},
        )
    )

    # Act
    job.status = AsyncJobStatus.COMPLETED
    job.output_data = {"created_count": 5, "updated_count": 2}
    result = repo.update(job)

    # Assert
    assert result.status == AsyncJobStatus.COMPLETED
    assert result.output_data == {"created_count": 5, "updated_count": 2}


# --- delete ---


@pytest.mark.integration
def test_delete_removes_job(session: Session) -> None:
    # Arrange
    _seed_users(session)
    course = _seed_course(session)
    repo = AsyncJobRepository(session)
    assert course.id is not None
    job = repo.create(
        AsyncJob(
            course_id=course.id,
            created_by_pid=123456789,
            kind="roster_upload",
            input_data={"csv_text": "data"},
        )
    )
    job_id = job.id

    # Act
    repo.delete(job)

    # Assert
    assert repo.get_by_id(job_id) is None  # type: ignore[arg-type]
