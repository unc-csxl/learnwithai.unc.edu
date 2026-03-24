from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from learnwithai.jobs import (
    EchoJob,
    JobPayload,
    NoopJobQueue,
    RosterUploadJob,
    job_adapter,
    job_handler_map,
    job_payload_adapter,
)
from learnwithai.jobs.echo import EchoJobHandler
from learnwithai.jobs.roster_upload import RosterUploadJobHandler


def test_jobs_package_exports_expected_symbols() -> None:
    # Arrange
    from learnwithai import jobs

    # Act
    exported_names = jobs.__all__

    # Assert
    assert exported_names == [
        "Job",
        "EchoJob",
        "NoopJobQueue",
        "RosterUploadJob",
        "JobPayload",
    ]


def test_job_payload_alias_is_annotated_union() -> None:
    # Arrange / Act
    import typing

    origin = typing.get_origin(JobPayload)

    # Assert — discriminated unions are wrapped in Annotated
    assert origin is typing.Annotated


def test_job_adapter_builds_echo_job_from_payload() -> None:
    # Arrange
    payload = {"type": "echo", "message": "hello"}

    # Act
    job = job_adapter(payload)

    # Assert
    assert isinstance(job, EchoJob)
    assert job.message == "hello"


def test_job_payload_adapter_builds_echo_job_from_payload() -> None:
    # Arrange
    payload = {"type": "echo", "message": "hello"}

    # Act
    job = job_payload_adapter.validate_python(payload)

    # Assert
    assert isinstance(job, EchoJob)
    assert job.message == "hello"


def test_job_adapter_rejects_unknown_job_type() -> None:
    # Arrange
    payload = {"type": "missing", "message": "hello"}

    # Act

    # Assert
    with pytest.raises(ValidationError):
        job_adapter(payload)


def test_job_handler_map_points_echo_job_to_echo_handler() -> None:
    # Arrange
    handler_class = job_handler_map[EchoJob]

    # Act
    handler = handler_class()

    # Assert
    assert isinstance(handler, EchoJobHandler)


def test_echo_job_handler_prints_payload_with_health_status() -> None:
    # Arrange
    job = EchoJob(message="hello")
    handler = EchoJobHandler()
    expected_status = {"status": "ok"}

    # Act
    with (
        patch("learnwithai.jobs.echo.get_health_status", return_value=expected_status),
        patch("builtins.print") as print_mock,
    ):
        handler.handle(job)

    # Assert
    print_mock.assert_called_once_with(
        {
            "task": "echo_job",
            "payload": job,
            "core_status": expected_status,
        }
    )


# ---- RosterUploadJob ----


def test_job_adapter_builds_roster_upload_job_from_payload() -> None:
    # Arrange
    payload = {"type": "roster_upload", "job_id": 42}

    # Act
    job = job_adapter(payload)

    # Assert
    assert isinstance(job, RosterUploadJob)
    assert job.job_id == 42


def test_job_handler_map_points_roster_upload_to_handler() -> None:
    # Arrange
    handler_class = job_handler_map[RosterUploadJob]

    # Act
    handler = handler_class()

    # Assert
    assert isinstance(handler, RosterUploadJobHandler)


def test_noop_job_queue_enqueue_does_nothing() -> None:
    # Arrange
    queue = NoopJobQueue()
    job = RosterUploadJob(job_id=1)

    # Act / Assert — must not raise
    queue.enqueue(job)


def test_noop_job_queue_satisfies_job_queue_protocol() -> None:
    from learnwithai.interfaces import JobQueue

    assert isinstance(NoopJobQueue(), JobQueue)


def test_roster_upload_job_handler_commits_on_success() -> None:
    # Arrange
    job_payload = RosterUploadJob(job_id=42)
    handler = RosterUploadJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_svc = MagicMock()

    with (
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.services.roster_upload_service.RosterUploadService",
            return_value=mock_svc,
        ),
        patch(
            "learnwithai.repositories.roster_upload_repository.RosterUploadRepository"
        ),
        patch("learnwithai.repositories.user_repository.UserRepository"),
        patch("learnwithai.repositories.membership_repository.MembershipRepository"),
    ):
        handler.handle(job_payload)

    # Assert
    mock_svc.process_upload.assert_called_once_with(42)
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    mock_svc.mark_failed.assert_not_called()


def test_roster_upload_job_handler_rolls_back_and_marks_failed_on_error() -> None:
    # Arrange
    job_payload = RosterUploadJob(job_id=42)
    handler = RosterUploadJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_svc = MagicMock()
    mock_svc.process_upload.side_effect = RuntimeError("boom")

    with (
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.services.roster_upload_service.RosterUploadService",
            return_value=mock_svc,
        ),
        patch(
            "learnwithai.repositories.roster_upload_repository.RosterUploadRepository"
        ),
        patch("learnwithai.repositories.user_repository.UserRepository"),
        patch("learnwithai.repositories.membership_repository.MembershipRepository"),
        pytest.raises(RuntimeError, match="boom"),
    ):
        handler.handle(job_payload)

    # Assert
    mock_session.rollback.assert_called_once()
    mock_svc.mark_failed.assert_called_once_with(42)
