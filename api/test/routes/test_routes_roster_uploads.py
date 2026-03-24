"""Tests for roster upload route handlers."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from api.routes.roster_uploads import get_roster_upload_status, upload_roster_csv
from api.models import RosterUploadResponse, RosterUploadStatusResponse
from learnwithai.errors import AuthorizationError
from learnwithai.tables.roster_upload_job import RosterUploadJob, RosterUploadStatus


# ---- helpers ----


def _stub_user(pid: int = 123456789) -> MagicMock:
    mock = MagicMock()
    mock.pid = pid
    return mock


def _stub_course(course_id: int = 1) -> MagicMock:
    mock = MagicMock()
    mock.id = course_id
    return mock


def _make_upload_file(
    content: str = "Student,ID,SIS User ID,SIS Login ID\n",
    content_type: str = "text/csv",
    filename: str = "roster.csv",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content.encode("utf-8")),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def _stub_job(
    job_id: int = 1,
    course_id: int = 1,
    status: RosterUploadStatus = RosterUploadStatus.PENDING,
) -> MagicMock:
    mock = MagicMock(spec=RosterUploadJob)
    mock.id = job_id
    mock.course_id = course_id
    mock.status = status
    mock.uploaded_by_pid = 123456789
    mock.csv_data = "data"
    mock.created_count = 0
    mock.updated_count = 0
    mock.error_count = 0
    mock.error_details = None
    mock.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock.completed_at = None
    return mock


# ---- upload_roster_csv ----


@pytest.mark.anyio
async def test_upload_roster_csv_returns_accepted_response() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    upload_repo = MagicMock()
    job_queue = MagicMock()
    created_job = _stub_job(job_id=42)
    upload_repo.create.return_value = created_job
    file = _make_upload_file()

    # Act
    result = await upload_roster_csv(
        subject, course, course_svc, upload_repo, job_queue, file
    )

    # Assert
    assert isinstance(result, RosterUploadResponse)
    assert result.id == 42
    assert result.status == RosterUploadStatus.PENDING
    course_svc.authorize_instructor.assert_called_once_with(subject, course)
    upload_repo.create.assert_called_once()
    job_queue.enqueue.assert_called_once()


@pytest.mark.anyio
async def test_upload_roster_csv_rejects_non_csv_content_type() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    upload_repo = MagicMock()
    job_queue = MagicMock()
    file = _make_upload_file(content_type="application/json")

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        await upload_roster_csv(
            subject, course, course_svc, upload_repo, job_queue, file
        )
    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_upload_roster_csv_rejects_non_utf8_file() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    upload_repo = MagicMock()
    job_queue = MagicMock()
    bad_bytes = b"\xff\xfe"
    file = UploadFile(
        file=BytesIO(bad_bytes),
        filename="roster.csv",
        headers=Headers({"content-type": "text/csv"}),
    )

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        await upload_roster_csv(
            subject, course, course_svc, upload_repo, job_queue, file
        )
    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_upload_roster_csv_raises_403_for_non_instructor() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    course_svc.authorize_instructor.side_effect = AuthorizationError("nope")
    upload_repo = MagicMock()
    job_queue = MagicMock()
    file = _make_upload_file()

    # Act / Assert
    with pytest.raises(AuthorizationError):
        await upload_roster_csv(
            subject, course, course_svc, upload_repo, job_queue, file
        )


# ---- get_roster_upload_status ----


def test_get_roster_upload_status_returns_status() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    upload_repo = MagicMock()
    job = _stub_job(job_id=42, course_id=1, status=RosterUploadStatus.COMPLETED)
    job.created_count = 5
    job.updated_count = 2
    job.error_count = 1
    job.error_details = "PID 999: error"
    job.completed_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    upload_repo.get_by_id.return_value = job

    # Act
    result = get_roster_upload_status(subject, course, course_svc, upload_repo, 42)

    # Assert
    assert isinstance(result, RosterUploadStatusResponse)
    assert result.id == 42
    assert result.status == RosterUploadStatus.COMPLETED
    assert result.created_count == 5
    assert result.error_details == "PID 999: error"


def test_get_roster_upload_status_returns_404_when_not_found() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    upload_repo = MagicMock()
    upload_repo.get_by_id.return_value = None

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        get_roster_upload_status(subject, course, course_svc, upload_repo, 999)
    assert exc_info.value.status_code == 404


def test_get_roster_upload_status_returns_404_for_wrong_course() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    upload_repo = MagicMock()
    job = _stub_job(job_id=42, course_id=99)
    upload_repo.get_by_id.return_value = job

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        get_roster_upload_status(subject, course, course_svc, upload_repo, 42)
    assert exc_info.value.status_code == 404


def test_get_roster_upload_status_raises_403_for_non_instructor() -> None:
    # Arrange
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    course_svc.authorize_instructor.side_effect = AuthorizationError("nope")
    upload_repo = MagicMock()

    # Act / Assert
    with pytest.raises(AuthorizationError):
        get_roster_upload_status(subject, course, course_svc, upload_repo, 42)
