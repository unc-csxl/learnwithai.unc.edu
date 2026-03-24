from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from learnwithai.jobs import (
    EchoJob,
    JobPayload,
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
    assert exported_names == ["Job", "EchoJob", "RosterUploadJob", "JobPayload"]


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


def test_roster_upload_job_handler_calls_process_roster_upload() -> None:
    # Arrange
    job = RosterUploadJob(job_id=42)
    handler = RosterUploadJobHandler()

    # Act
    with patch("learnwithai.jobs.roster_upload.process_roster_upload") as mock_process:
        handler.handle(job)

    # Assert
    mock_process.assert_called_once_with(42)
