from __future__ import annotations

import pytest

from learnwithai.config import Settings, get_settings


def test_effective_database_url_uses_explicit_database_url() -> None:
    # Arrange
    settings = Settings(database_url="sqlite:///explicit.db", _env_file=None)

    # Act
    database_url = settings.effective_database_url

    # Assert
    assert database_url == "sqlite:///explicit.db"


def test_effective_database_url_uses_test_default_for_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(environment="test", _env_file=None)

    # Act
    database_url = settings.effective_database_url

    # Assert
    assert database_url.endswith("/learnwithai_test")


def test_effective_database_url_uses_default_for_non_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(environment="development", _env_file=None)

    # Act
    database_url = settings.effective_database_url

    # Assert
    assert database_url.endswith("/learnwithai")


def test_effective_rabbitmq_url_uses_explicit_value() -> None:
    # Arrange
    settings = Settings(rabbitmq_url="amqp://custom-host/", _env_file=None)

    # Act
    rabbitmq_url = settings.effective_rabbitmq_url

    # Assert
    assert rabbitmq_url == "amqp://custom-host/"


def test_effective_rabbitmq_url_uses_default_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    settings = Settings(_env_file=None)

    # Act
    rabbitmq_url = settings.effective_rabbitmq_url

    # Assert
    assert rabbitmq_url == "amqp://guest:guest@rabbitmq:5672/"


def test_environment_flags_reflect_current_environment() -> None:
    # Arrange
    development_settings = Settings(environment="development", _env_file=None)
    test_settings = Settings(environment="test", _env_file=None)
    production_settings = Settings(environment="production", _env_file=None)

    # Act
    development_flags = (
        development_settings.is_development,
        development_settings.is_test,
        development_settings.is_production,
    )
    test_flags = (
        test_settings.is_development,
        test_settings.is_test,
        test_settings.is_production,
    )
    production_flags = (
        production_settings.is_development,
        production_settings.is_test,
        production_settings.is_production,
    )

    # Assert
    assert development_flags == (True, False, False)
    assert test_flags == (False, True, False)
    assert production_flags == (False, False, True)


def test_get_settings_returns_cached_settings_instance() -> None:
    # Arrange
    get_settings.cache_clear()

    # Act
    first_settings = get_settings()
    second_settings = get_settings()

    # Assert
    assert first_settings is second_settings