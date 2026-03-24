"""Tests for Canvas CSV parsing and roster import service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from learnwithai.services.roster_upload_service import (
    ImportResult,
    ParsedStudent,
    _do_process,
    _import_students,
    _mark_failed,
    parse_canvas_csv,
    process_roster_upload,
)
from learnwithai.tables.membership import MembershipState, MembershipType
from learnwithai.tables.roster_upload_job import RosterUploadJob, RosterUploadStatus

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "rosters"


# ---- parse_canvas_csv ----


def test_parse_canvas_csv_extracts_student_from_populated_gradesheet() -> None:
    # Arrange
    csv_text = (DATA_DIR / "sample_populated_canvas_gradesheet.csv").read_text()

    # Act
    students = parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 1
    assert students[0].family_name == "Jordan"
    assert students[0].given_name == "Kris"
    assert students[0].pid == 710453084
    assert students[0].onyen == "krisj"


def test_parse_canvas_csv_extracts_student_from_empty_gradesheet() -> None:
    # Arrange
    csv_text = (DATA_DIR / "sample_empty_canvas_gradesheet.csv").read_text()

    # Act
    students = parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 1
    assert students[0].family_name == "Jordan"
    assert students[0].given_name == "Kris"
    assert students[0].pid == 710453084
    assert students[0].onyen == "Kris"


def test_parse_canvas_csv_skips_rows_with_missing_sis_fields() -> None:
    # Arrange
    csv_text = "Student,ID,SIS User ID,SIS Login ID\n" "John Doe,1,,\n"

    # Act
    students = parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 0


def test_parse_canvas_csv_skips_non_numeric_pid() -> None:
    # Arrange
    csv_text = (
        "Student,ID,SIS User ID,SIS Login ID\n" '"Doe, Jane",1,abc,jdoe\n'
    )

    # Act
    students = parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 0


def test_parse_canvas_csv_raises_on_missing_columns() -> None:
    # Arrange
    csv_text = "Name,ID\nJohn,1\n"

    # Act / Assert
    with pytest.raises(ValueError, match="CSV missing required columns"):
        parse_canvas_csv(csv_text)


def test_parse_canvas_csv_handles_name_without_comma() -> None:
    # Arrange
    csv_text = (
        "Student,ID,SIS User ID,SIS Login ID\n" "SingleName,1,999999999,sname\n"
    )

    # Act
    students = parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 1
    assert students[0].family_name == "SingleName"
    assert students[0].given_name == ""


def test_parse_canvas_csv_returns_empty_for_headers_only() -> None:
    # Arrange
    csv_text = "Student,ID,SIS User ID,SIS Login ID\n"

    # Act
    students = parse_canvas_csv(csv_text)

    # Assert
    assert len(students) == 0


# ---- _import_students ----


def test_import_students_creates_new_user_and_membership() -> None:
    # Arrange
    session = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course_ids.return_value = None
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    with (
        patch(
            "learnwithai.services.roster_upload_service.UserRepository",
            return_value=user_repo,
        ),
        patch(
            "learnwithai.services.roster_upload_service.MembershipRepository",
            return_value=membership_repo,
        ),
    ):
        # Act
        result = _import_students(session, 1, [student])

    # Assert
    assert result.created == 1
    assert result.updated == 0
    assert result.errors == []
    user_repo.register_user.assert_called_once()
    membership_repo.create.assert_called_once()


def test_import_students_re_enrolls_dropped_membership() -> None:
    # Arrange
    session = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = MagicMock()
    existing = MagicMock()
    existing.state = MembershipState.DROPPED
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course_ids.return_value = existing
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    with (
        patch(
            "learnwithai.services.roster_upload_service.UserRepository",
            return_value=user_repo,
        ),
        patch(
            "learnwithai.services.roster_upload_service.MembershipRepository",
            return_value=membership_repo,
        ),
    ):
        # Act
        result = _import_students(session, 1, [student])

    # Assert
    assert result.updated == 1
    assert result.created == 0
    assert existing.state == MembershipState.ENROLLED
    session.flush.assert_called()


def test_import_students_skips_already_enrolled() -> None:
    # Arrange
    session = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = MagicMock()
    existing = MagicMock()
    existing.state = MembershipState.ENROLLED
    membership_repo = MagicMock()
    membership_repo.get_by_user_and_course_ids.return_value = existing
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    with (
        patch(
            "learnwithai.services.roster_upload_service.UserRepository",
            return_value=user_repo,
        ),
        patch(
            "learnwithai.services.roster_upload_service.MembershipRepository",
            return_value=membership_repo,
        ),
    ):
        # Act
        result = _import_students(session, 1, [student])

    # Assert
    assert result.created == 0
    assert result.updated == 0
    assert result.errors == []


def test_import_students_records_error_on_exception() -> None:
    # Arrange
    session = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.side_effect = RuntimeError("db error")
    membership_repo = MagicMock()
    student = ParsedStudent(
        family_name="Doe", given_name="Jane", pid=999999999, onyen="jdoe"
    )

    with (
        patch(
            "learnwithai.services.roster_upload_service.UserRepository",
            return_value=user_repo,
        ),
        patch(
            "learnwithai.services.roster_upload_service.MembershipRepository",
            return_value=membership_repo,
        ),
    ):
        # Act
        result = _import_students(session, 1, [student])

    # Assert
    assert len(result.errors) == 1
    assert "999999999" in result.errors[0]


# ---- _do_process ----


def test_do_process_parses_csv_and_updates_job() -> None:
    # Arrange
    session = MagicMock()
    job = MagicMock(spec=RosterUploadJob)
    job.csv_data = "Student,ID,SIS User ID,SIS Login ID\n"
    job.course_id = 1
    repo = MagicMock()
    repo.get_by_id.return_value = job

    with (
        patch(
            "learnwithai.services.roster_upload_service.RosterUploadRepository",
            return_value=repo,
        ),
        patch(
            "learnwithai.services.roster_upload_service._import_students",
            return_value=ImportResult(created=2, updated=1, errors=["err"]),
        ) as mock_import,
    ):
        # Act
        _do_process(session, 42)

    # Assert
    assert job.status == RosterUploadStatus.COMPLETED
    assert job.created_count == 2
    assert job.updated_count == 1
    assert job.error_count == 1
    assert job.error_details == "err"
    assert job.completed_at is not None
    mock_import.assert_called_once()


def test_do_process_raises_when_job_not_found() -> None:
    # Arrange
    session = MagicMock()
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with patch(
        "learnwithai.services.roster_upload_service.RosterUploadRepository",
        return_value=repo,
    ):
        # Act / Assert
        with pytest.raises(ValueError, match="not found"):
            _do_process(session, 999)


def test_do_process_sets_no_error_details_when_no_errors() -> None:
    # Arrange
    session = MagicMock()
    job = MagicMock(spec=RosterUploadJob)
    job.csv_data = "Student,ID,SIS User ID,SIS Login ID\n"
    job.course_id = 1
    repo = MagicMock()
    repo.get_by_id.return_value = job

    with (
        patch(
            "learnwithai.services.roster_upload_service.RosterUploadRepository",
            return_value=repo,
        ),
        patch(
            "learnwithai.services.roster_upload_service._import_students",
            return_value=ImportResult(created=0, updated=0, errors=[]),
        ),
    ):
        # Act
        _do_process(session, 1)

    # Assert
    assert job.error_details is None


# ---- _mark_failed ----


def test_mark_failed_sets_status_to_failed() -> None:
    # Arrange
    session = MagicMock()
    job = MagicMock(spec=RosterUploadJob)
    repo = MagicMock()
    repo.get_by_id.return_value = job

    with patch(
        "learnwithai.services.roster_upload_service.RosterUploadRepository",
        return_value=repo,
    ):
        # Act
        _mark_failed(session, 42)

    # Assert
    assert job.status == RosterUploadStatus.FAILED
    assert job.completed_at is not None


def test_mark_failed_does_nothing_when_job_not_found() -> None:
    # Arrange
    session = MagicMock()
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with patch(
        "learnwithai.services.roster_upload_service.RosterUploadRepository",
        return_value=repo,
    ):
        # Act (should not raise)
        _mark_failed(session, 999)


def test_mark_failed_swallows_exceptions() -> None:
    # Arrange
    session = MagicMock()
    repo = MagicMock()
    repo.get_by_id.side_effect = RuntimeError("db gone")

    with patch(
        "learnwithai.services.roster_upload_service.RosterUploadRepository",
        return_value=repo,
    ):
        # Act (should not raise)
        _mark_failed(session, 42)


# ---- process_roster_upload ----


def test_process_roster_upload_commits_on_success() -> None:
    # Arrange
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()

    with (
        patch(
            "learnwithai.services.roster_upload_service.get_engine",
            return_value=mock_engine,
        ),
        patch(
            "sqlmodel.Session",
            return_value=mock_session,
        ),
        patch(
            "learnwithai.services.roster_upload_service._do_process",
        ) as mock_do,
    ):
        # Act
        process_roster_upload(42)

    # Assert
    mock_do.assert_called_once_with(mock_session, 42)
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


def test_process_roster_upload_rolls_back_and_marks_failed_on_error() -> None:
    # Arrange
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()

    with (
        patch(
            "learnwithai.services.roster_upload_service.get_engine",
            return_value=mock_engine,
        ),
        patch(
            "sqlmodel.Session",
            return_value=mock_session,
        ),
        patch(
            "learnwithai.services.roster_upload_service._do_process",
            side_effect=RuntimeError("boom"),
        ),
        patch(
            "learnwithai.services.roster_upload_service._mark_failed",
        ) as mock_fail,
        pytest.raises(RuntimeError, match="boom"),
    ):
        # Act
        process_roster_upload(42)

    # Assert
    mock_session.rollback.assert_called_once()
    mock_fail.assert_called_once_with(mock_session, 42)
