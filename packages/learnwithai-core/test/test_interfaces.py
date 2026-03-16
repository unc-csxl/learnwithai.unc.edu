from __future__ import annotations

from pydantic import BaseModel

import learnwithai
from learnwithai.config import Settings
from learnwithai.interfaces import Job
from learnwithai.jobs.echo import EchoJob


class DummyJob(Job):
    type: str = "dummy"


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

    # Assert
    assert exported_names == ["JobQueue", "JobHandler", "Job"]
    assert issubclass(exported_job_class, BaseModel)


def test_get_job_types_includes_known_and_new_subclasses() -> None:
    # Arrange
    known_job_types = {job_type.__name__ for job_type in Job.get_job_types()}

    # Act
    has_echo_job = EchoJob in Job.get_job_types()
    has_dummy_job = DummyJob in Job.get_job_types()

    # Assert
    assert "EchoJob" in known_job_types
    assert has_echo_job is True
    assert has_dummy_job is True