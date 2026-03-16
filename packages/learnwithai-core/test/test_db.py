from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from learnwithai import db


def test_get_engine_builds_engine_from_settings() -> None:
    # Arrange
    expected_settings = SimpleNamespace(
        effective_database_url="sqlite:///test.db",
        db_echo=True,
    )

    # Act
    with patch("learnwithai.db.get_settings", return_value=expected_settings), patch(
        "learnwithai.db.create_engine", return_value="engine"
    ) as create_engine_mock:
        db.get_engine.cache_clear()
        engine = db.get_engine()

    # Assert
    assert engine == "engine"
    create_engine_mock.assert_called_once_with("sqlite:///test.db", echo=True)


def test_get_engine_returns_cached_engine() -> None:
    # Arrange
    expected_settings = SimpleNamespace(
        effective_database_url="sqlite:///test.db",
        db_echo=False,
    )

    # Act
    with patch("learnwithai.db.get_settings", return_value=expected_settings), patch(
        "learnwithai.db.create_engine", return_value="engine"
    ) as create_engine_mock:
        db.get_engine.cache_clear()
        first_engine = db.get_engine()
        second_engine = db.get_engine()

    # Assert
    assert first_engine == second_engine == "engine"
    create_engine_mock.assert_called_once_with("sqlite:///test.db", echo=False)


def test_create_db_and_tables_uses_cached_engine() -> None:
    # Arrange
    expected_engine = object()

    # Act
    with patch("learnwithai.db.get_engine", return_value=expected_engine), patch(
        "learnwithai.db.SQLModel.metadata.create_all"
    ) as create_all_mock:
        db.create_db_and_tables()

    # Assert
    create_all_mock.assert_called_once_with(expected_engine)


def test_get_session_builds_session_from_engine() -> None:
    # Arrange
    expected_engine = object()

    # Act
    with patch("learnwithai.db.get_engine", return_value=expected_engine), patch(
        "learnwithai.db.Session", return_value="session"
    ) as session_mock:
        session = db.get_session()

    # Assert
    assert session == "session"
    session_mock.assert_called_once_with(expected_engine)