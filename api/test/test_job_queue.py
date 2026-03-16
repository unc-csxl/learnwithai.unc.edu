from __future__ import annotations

from unittest.mock import patch, MagicMock

from api.dependency_injection import (
    job_queue_factory,
    settings_factory,
    user_repository_factory,
    csxl_auth_service_factory,
)


def test_settings_factory_returns_settings_instance() -> None:
    # Arrange / Act
    settings = settings_factory()

    # Assert
    assert settings.app_name == "learnwithai"


def test_user_repository_factory_builds_repository_with_session() -> None:
    # Arrange
    session = MagicMock()

    # Act
    repo = user_repository_factory(session)

    # Assert
    assert repo._session is session


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
        "api.dependency_injection.DramatiqJobQueue", return_value=expected_queue
    ) as queue_class_mock:
        job_queue = job_queue_factory()

    # Assert
    assert job_queue is expected_queue
    queue_class_mock.assert_called_once_with()
