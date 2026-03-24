"""Tests for Canvas CSV parsing and roster import service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from learnwithai.services.roster_upload_service import (
    ImportResult,
    ParsedStudent,
    RosterUploadService,
)
from learnwithai.tables.membership import MembershipState
from learnwithai.tables.roster_upload_job import RosterUploadJob, RosterUploadStatus

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "rosters"


# ---- helpers ----


def _make_service(
    upload_repo: MagicMock | None = None,
    user_repo: MagicMock | None = None,
    membership_repo: MagicMock | None = None,
    job_queue: MagicMock | None = None,
) -> RosterUploadService:
    return RosterUploadService(
        upload_repo=upload_repo or MagicMock(),
        user_repo=user_repo or MagicMock(),
        membership_repo=membership_repo or MagicMock(),
        job_queue=job_queue or MagicMock(),
    )


# ---- RosterUploadService._parse_canvas_csv ----


def test_parse_canvas_csv_extracts_student_from_populated_gradesheet() -> None:
    # Arrange
    csv_text = (DATA_DIR / "sample_populated_canvas_gradesheet.csv").read_text()
    svc = _make_service()

    # Act
    students = svc._parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 1
    assert students[0].family_name == "Jordan"
    assert students[0].given_name == "Kris"
    assert students[0].pid == 710453084
    assert students[0].onyen == "krisj"


def test_parse_canvas_csv_extracts_student_from_empty_gradesheet() -> None:
    # Arrange
    csv_text = (DATA_DIR / "sample_empty_canvas_gradesheet.csv").read_text()
    svc = _make_service()

    # Act
    students = svc._parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 1
    assert students[0].family_name == "Jordan"
    assert students[0].given_name == "Kris"
    assert students[0].pid == 710453084
    assert students[0].onyen == "Kris"


def test_parse_canvas_csv_skips_rows_with_missing_sis_fields() -> None:
    # Arrange
    csv_text = "Student,ID,SIS User ID,SIS Login ID\nJohn Doe,1,,\n"
    svc = _make_service()

    # Act
    students = svc._parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 0


def test_parse_canvas_csv_skips_non_numeric_pid() -> None:
    # Arrange
    csv_text = 'Student,ID,SIS User ID,SIS Login ID\n"Doe, Jane",1,abc,jdoe\n'
    svc = _make_service()

    # Act
    students = svc._parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 0


def test_parse_canvas_csv_raises_on_missing_columns() -> None:
    # Arrange
    csv_text = "Name,ID\nJohn,1\n"
    svc = _make_service()

    # Act / Assert
    with pytest.raises(ValueError, match="CSV missing required columns"):
        svc._parse_canvas_csv(csv_text)


def test_parse_canvas_csv_handles_name_without_comma() -> None:
    # Arrange
    csv_text = "Student,ID,SIS User ID,SIS Login ID\nSingleName,1,999999999,sname\n"
    svc = _make_service()

    # Act
    students = svc._parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 1
    assert students[0].family_name == "SingleName"
    assert students[0].given_name == ""


def test_parse_canvas_csv_returns_empty_for_headers_only() -> None:
    # Arrange
    csv_text = "Student,ID,SIS User ID,SIS Login ID\n"
    svc = _make_service()

    # Act
    students = svc._parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 0


# ---- RosterUploadService.submit_upload ----


def test_submit_upload_creates_job_and_enqueues() -> None:
    # Arrange
    subject = MagicMock()
    subject.pid = 123456789
    created_job = MagicMock(spec=RosterUploadJob)
    created_job.id = 42
    upload_repo = MagicMock()
    upload_repo.create.return_value = created_job
    job_queue = MagicMock()
    svc = _make_service(upload_repo=upload_repo, job_queue=job_queue)

    # Act
    with patch(
        "learnwithai.services.roster_upload_service.RosterUploadJob"
    ) as mock_job_cls:
        mock_job_cls.return_value = MagicMock()
        result = svc.submit_upload(subject, course_id=1, csv_text="data")

    # Assert
    assert result is created_job
    upload_repo.create.assert_called_once()
    job_queue.enqueue.assert_called_once()


# ---- RosterUploadService.process_upload ----


def test_process_upload_parses_csv_and_updates_job() -> None:
    # Arrange
    job = MagicMock(spec=RosterUploadJob)
    job.csv_data = "Student,ID,SIS User ID,SIS Login ID\n"
    job.course_id = 1
    upload_repo = MagicMock()
    upload_repo.get_by_id.return_value = job
    svc = _make_service(upload_repo=upload_repo)

    with patch.object(
        svc,
        "_import_students",
        return_value=ImportResult(created=2, updated=1, errors=["err"]),
    ) as mock_import:
        # Act
        svc.process_upload(42)

    # Assert
    assert job.status == RosterUploadStatus.COMPLETED
    assert job.created_count == 2
    assert job.updated_count == 1
    assert job.error_count == 1
    assert job.error_details == "err"
    assert job.completed_at is not None
    mock_import.assert_called_once()


def test_process_upload_raises_when_job_not_found() -> None:
    # Arrange
    upload_repo = MagicMock()
    upload_repo.get_by_id.return_value = None
    svc = _make_service(upload_repo=upload_repo)

    # Act / Assert
    with pytest.raises(ValueError, match="not found"):
        svc.process_upload(999)


def test_process_upload_sets_no_error_details_when_no_errors() -> None:
    # Arrange
    job = MagicMock(spec=RosterUploadJob)
    job.csv_data = "Student,ID,SIS User ID,SIS Login ID\n"
    job.course_id = 1
    upload_repo = MagicMock()
    upload_repo.get_by_id.return_value = job
    svc = _make_service(upload_repo=upload_repo)

    with patch.object(
        svc,
        "_import_students",
        return_value=ImportResult(created=0, updated=0, errors=[]),
    ):
        # Act
        svc.process_upload(1)

    # Assert
    assert job.error_details is None


# ---- RosterUploadService.mark_failed ----


def test_mark_failed_sets_status_to_failed() -> None:
    # Arrange
    job = MagicMock(spec=RosterUploadJob)
    upload_repo = MagicMock()
    upload_repo.get_by_id.return_value = job
    svc = _make_service(upload_repo=upload_repo)

    # Act
    svc.mark_failed(42)

    # Assert
    assert job.status == RosterUploadStatus.FAILED
    assert job.completed_at is not None
    upload_repo.update.assert_called_once_with(job)


def test_mark_failed_does_nothing_when_job_not_found() -> None:
    # Arrange
    upload_repo = MagicMock()
    upload_repo.get_by_id.return_value = None
    svc = _make_service(upload_repo=upload_repo)

    # Act (should not raise)
    svc.mark_failed(999)

    upload_repo.update.assert_not_called()


def test_mark_failed_swallows_exceptions() -> None:
    # Arrange
    upload_repo = MagicMock()
    upload_repo.get_by_id.side_effect = RuntimeError("db gone")
    svc = _make_service(upload_repo=upload_repo)

    # Act (should not raise)
    svc.mark_failed(42)


# ---- RosterUploadService._import_students ----


def test_import_students_creates_new_user_and_membership() -> None:
    # Arrange
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course_ids.return_value = None
    svc = _make_service(user_repo=user_repo, membership_repo=membership_repo)
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    # Act
    result = svc._import_students(1, [student])

    # Assert
    assert result.created == 1
    assert result.updated == 0
    assert result.errors == []
    user_repo.register_user.assert_called_once()
    membership_repo.create.assert_called_once()


def test_import_students_re_enrolls_dropped_membership() -> None:
    # Arrange
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = MagicMock()
    existing = MagicMock()
    existing.state = MembershipState.DROPPED
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course_ids.return_value = existing
    svc = _make_service(user_repo=user_repo, membership_repo=membership_repo)
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    # Act
    result = svc._import_students(1, [student])

    # Assert
    assert result.updated == 1
    assert result.created == 0
    assert existing.state == MembershipState.ENROLLED
    membership_repo.update.assert_called_once_with(existing)


def test_import_students_skips_already_enrolled() -> None:
    # Arrange
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = MagicMock()
    existing = MagicMock()
    existing.state = MembershipState.ENROLLED
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course_ids.return_value = existing
    svc = _make_service(user_repo=user_repo, membership_repo=membership_repo)
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    # Act
    result = svc._import_students(1, [student])

    # Assert
    assert result.created == 0
    assert result.updated == 0
    assert result.errors == []


def test_import_students_records_error_on_exception() -> None:
    # Arrange
    user_repo = MagicMock()
    user_repo.get_by_pid.side_effect = RuntimeError("db error")
    svc = _make_service(user_repo=user_repo)
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    # Act
    result = svc._import_students(1, [student])

    # Assert
    assert len(result.errors) == 1
    assert "999999999" in result.errors[0]
