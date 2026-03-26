from __future__ import annotations

from unittest.mock import MagicMock, patch

from api.di import (
    csxl_auth_service_factory,
    job_queue_factory,
)


def test_csxl_auth_service_factory_builds_service_with_dependencies() -> None:
    # Arrange
    settings = MagicMock()
    user_repo = MagicMock()

    # Act
    service = csxl_auth_service_factory(settings, user_repo)

    # Assert
    assert service._settings is settings
    assert service._user_repo is user_repo


def test_job_queue_factory_builds_dramatiq_job_queue() -> None:
    # Arrange
    expected_queue = object()

    # Act
    with patch(
        "api.di.DramatiqJobQueue", return_value=expected_queue
    ) as queue_class_mock:
        job_queue = job_queue_factory()

    # Assert
    assert job_queue is expected_queue
    queue_class_mock.assert_called_once_with()
