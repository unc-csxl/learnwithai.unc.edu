# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from learnwithai.config import ENV_FILE_NAME, Settings, find_env_file, get_settings


def build_settings(**overrides: Any) -> Settings:
    settings_data = {
        "app_name": "learnwithai",
        "environment": "development",
        "database_url": None,
        "db_echo": False,
        "rabbitmq_url": None,
        "api_host": "0.0.0.0",
        "api_port": 8000,
        "log_level": "INFO",
    }
    settings_data.update(overrides)
    return Settings.model_construct(**settings_data)


def test_effective_database_url_uses_explicit_database_url() -> None:
    # Arrange
    settings = build_settings(database_url="sqlite:///explicit.db")

    # Act
    database_url = settings.effective_database_url

    # Assert
    assert database_url == "sqlite:///explicit.db"


def test_effective_database_url_uses_test_default_for_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = build_settings(environment="test")

    # Act
    database_url = settings.effective_database_url

    # Assert
    assert database_url.endswith("/learnwithai_test")


def test_effective_database_url_uses_default_for_non_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = build_settings(environment="development")

    # Act
    database_url = settings.effective_database_url

    # Assert
    assert database_url.endswith("/learnwithai")


def test_effective_rabbitmq_url_uses_explicit_value() -> None:
    # Arrange
    settings = build_settings(rabbitmq_url="amqp://custom-host/")

    # Act
    rabbitmq_url = settings.effective_rabbitmq_url

    # Assert
    assert rabbitmq_url == "amqp://custom-host/"


def test_effective_rabbitmq_url_uses_default_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("RABBITMQ_URL", raising=False)
    settings = build_settings()

    # Act
    rabbitmq_url = settings.effective_rabbitmq_url

    # Assert
    assert rabbitmq_url == "amqp://guest:guest@rabbitmq:5672/"


def test_environment_flags_reflect_current_environment() -> None:
    # Arrange
    development_settings = build_settings(environment="development")
    test_settings = build_settings(environment="test")
    production_settings = build_settings(environment="production")

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


def test_find_env_file_returns_nearest_parent_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    repo_dir = tmp_path / "repo"
    nested_dir = repo_dir / "packages" / "learnwithai-core"
    nested_dir.mkdir(parents=True)
    env_file = repo_dir / ENV_FILE_NAME
    env_file.write_text("LOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.chdir(nested_dir)

    # Act
    discovered_env_file = find_env_file()

    # Assert
    assert discovered_env_file == env_file


def test_settings_load_from_nearest_parent_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    repo_dir = tmp_path / "repo"
    nested_dir = repo_dir / "packages" / "learnwithai-core"
    nested_dir.mkdir(parents=True)
    env_file = repo_dir / ENV_FILE_NAME
    env_file.write_text("LOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.chdir(nested_dir)

    # Act
    settings = Settings()

    # Assert
    assert settings.log_level == "DEBUG"


def test_settings_require_env_file_in_development(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    working_dir = tmp_path / "repo" / "packages" / "learnwithai-core"
    working_dir.mkdir(parents=True)
    monkeypatch.chdir(working_dir)
    monkeypatch.setenv("ENVIRONMENT", "development")

    # Act / Assert
    with pytest.raises(FileNotFoundError, match="Copy .env.example to .env"):
        Settings()


def test_settings_allow_missing_env_file_outside_development(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    working_dir = tmp_path / "repo" / "packages" / "learnwithai-core"
    working_dir.mkdir(parents=True)
    monkeypatch.chdir(working_dir)

    # Act
    settings = Settings(environment="test")

    # Assert
    assert settings.environment == "test"


def test_settings_accepts_azure_openai_env_var_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "teaching-assistant")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    # Act
    settings = Settings()

    # Assert
    assert settings.openai_api_key == "azure-key"
    assert settings.openai_model == "teaching-assistant"
    assert settings.openai_endpoint == "https://example.azure.com"
    assert settings.openai_api_version == "2024-10-21"


def test_azure_openai_env_vars_take_precedence_over_legacy_names(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("OPENAI_API_KEY", "repo-key")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")

    # Act
    settings = Settings()

    # Assert
    assert settings.openai_api_key == "azure-key"
