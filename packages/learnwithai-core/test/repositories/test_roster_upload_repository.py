"""Integration tests for roster upload repository."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from learnwithai.repositories.roster_upload_repository import RosterUploadRepository
from learnwithai.tables.course import Course, Term
from learnwithai.tables.roster_upload_job import RosterUploadJob, RosterUploadStatus


def _seed_course(session: Session) -> Course:
    course = Course(
        course_number="COMP101", name="Intro to CS", term=Term.FALL, year=2026
    )
    session.add(course)
    session.flush()
    return course


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_job(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = RosterUploadRepository(session)
    assert course.id is not None
    job = RosterUploadJob(
        course_id=course.id,
        uploaded_by_pid=123456789,
        csv_data="header\nrow",
    )

    # Act
    result = repo.create(job)

    # Assert
    assert result.id is not None
    assert result.course_id == course.id
    assert result.uploaded_by_pid == 123456789
    assert result.status == RosterUploadStatus.PENDING
    assert result.csv_data == "header\nrow"


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_job(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = RosterUploadRepository(session)
    assert course.id is not None
    created = repo.create(
        RosterUploadJob(
            course_id=course.id,
            uploaded_by_pid=123456789,
            csv_data="data",
        )
    )

    # Act
    result = repo.get_by_id(created.id)  # type: ignore[arg-type]

    # Assert
    assert result is not None
    assert result.id == created.id


@pytest.mark.integration
def test_get_by_id_returns_none_for_missing(session: Session) -> None:
    # Arrange
    repo = RosterUploadRepository(session)

    # Act
    result = repo.get_by_id(99999)

    # Assert
    assert result is None


# --- list_by_course ---


@pytest.mark.integration
def test_list_by_course_returns_all_jobs_for_course(
    session: Session,
) -> None:
    # Arrange
    course = _seed_course(session)
    repo = RosterUploadRepository(session)
    assert course.id is not None
    repo.create(
        RosterUploadJob(course_id=course.id, uploaded_by_pid=111, csv_data="first")
    )
    repo.create(
        RosterUploadJob(course_id=course.id, uploaded_by_pid=222, csv_data="second")
    )

    # Act
    results = repo.list_by_course(course.id)

    # Assert
    assert len(results) == 2
    csv_values = {r.csv_data for r in results}
    assert csv_values == {"first", "second"}


@pytest.mark.integration
def test_list_by_course_returns_empty_for_no_jobs(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = RosterUploadRepository(session)
    assert course.id is not None

    # Act
    results = repo.list_by_course(course.id)

    # Assert
    assert results == []


# --- update ---


@pytest.mark.integration
def test_update_modifies_job_status(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = RosterUploadRepository(session)
    assert course.id is not None
    job = repo.create(
        RosterUploadJob(
            course_id=course.id,
            uploaded_by_pid=123456789,
            csv_data="data",
        )
    )

    # Act
    job.status = RosterUploadStatus.COMPLETED
    job.created_count = 5
    result = repo.update(job)

    # Assert
    assert result.status == RosterUploadStatus.COMPLETED
    assert result.created_count == 5
