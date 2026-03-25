from __future__ import annotations

from pydantic import BaseModel

import learnwithai
from learnwithai.config import Settings
from learnwithai.interfaces import SupportsJobType
from learnwithai.jobs.echo import EchoJob


def test_package_exports_settings() -> None:
    # Arrange
    exported_names = learnwithai.__all__

    # Act
    exported_setting = learnwithai.Settings

    # Assert
    assert exported_names == ["Settings"]
    assert exported_setting is Settings


def test_interfaces_export_job_class() -> None:
    # Arrange
    from learnwithai import interfaces

    # Act
    exported_names = interfaces.__all__
    exported_job_class = interfaces.Job
    exported_job_type_protocol = interfaces.SupportsJobType
    exported_job_update = interfaces.JobUpdate
    exported_job_notifier = interfaces.JobNotifier

    # Assert
    assert exported_names == [
        "Job",
        "JobHandler",
        "JobNotifier",
        "JobQueue",
        "JobUpdate",
        "SupportsJobType",
        "TrackedJob",
    ]
    assert issubclass(exported_job_class, BaseModel)
    assert exported_job_type_protocol is SupportsJobType
    assert issubclass(exported_job_update, BaseModel)
    assert exported_job_notifier is not None


def test_echo_job_satisfies_read_only_job_type_protocol() -> None:
    # Arrange
    job = EchoJob(message="hello")

    # Act
    supports_job_type = isinstance(job, SupportsJobType)
    job_type = job.type

    # Assert
    assert supports_job_type is True
    assert job_type == "echo"
