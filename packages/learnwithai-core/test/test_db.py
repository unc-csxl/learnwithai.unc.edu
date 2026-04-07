# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from learnwithai import db


def test_get_engine_builds_engine_from_settings() -> None:
    # Arrange
    expected_settings = SimpleNamespace(
        effective_database_url="sqlite:///test.db",
        db_echo=True,
    )

    # Act
    with (
        patch("learnwithai.db.get_settings", return_value=expected_settings),
        patch("learnwithai.db.create_engine", return_value="engine") as create_engine_mock,
    ):
        db.get_engine.cache_clear()
        engine = db.get_engine()

    # Assert
    assert engine == "engine"
    create_engine_mock.assert_called_once_with(
        "sqlite:///test.db",
        echo=True,
        pool_pre_ping=True,
    )


def test_get_engine_returns_cached_engine() -> None:
    # Arrange
    expected_settings = SimpleNamespace(
        effective_database_url="sqlite:///test.db",
        db_echo=False,
    )

    # Act
    with (
        patch("learnwithai.db.get_settings", return_value=expected_settings),
        patch("learnwithai.db.create_engine", return_value="engine") as create_engine_mock,
    ):
        db.get_engine.cache_clear()
        first_engine = db.get_engine()
        second_engine = db.get_engine()

    # Assert
    assert first_engine == second_engine == "engine"
    create_engine_mock.assert_called_once_with(
        "sqlite:///test.db",
        echo=False,
        pool_pre_ping=True,
    )


def test_create_db_and_tables_uses_cached_engine() -> None:
    # Arrange
    expected_engine = object()

    # Act
    with (
        patch("learnwithai.db.load_table_metadata") as load_table_metadata_mock,
        patch("learnwithai.db.get_engine", return_value=expected_engine),
        patch("learnwithai.db.SQLModel.metadata.create_all") as create_all_mock,
    ):
        db.create_db_and_tables()

    # Assert
    load_table_metadata_mock.assert_called_once_with()
    create_all_mock.assert_called_once_with(expected_engine)


def test_load_table_metadata_imports_tables_package() -> None:
    # Act
    with patch("learnwithai.db.import_module") as import_module_mock:
        db.load_table_metadata()

    # Assert
    assert import_module_mock.call_count == 3
    import_module_mock.assert_any_call("learnwithai.tables")
    import_module_mock.assert_any_call("learnwithai.tools.jokes.tables")
    import_module_mock.assert_any_call("learnwithai.activities.iyow.tables")


def test_reset_db_and_tables_resets_postgresql_database_and_recreates_tables() -> None:
    # Arrange
    expected_settings = SimpleNamespace(
        effective_database_url=("postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai")
    )
    engine = MagicMock()

    # Act
    with (
        patch("learnwithai.db.get_settings", return_value=expected_settings),
        patch("learnwithai.db.get_engine", return_value=engine),
        patch("learnwithai.db._reset_postgresql_database") as reset_postgres_mock,
        patch("learnwithai.db.create_db_and_tables") as create_db_and_tables_mock,
    ):
        db.reset_db_and_tables()

    # Assert
    engine.dispose.assert_called_once_with()
    reset_postgres_mock.assert_called_once()
    create_db_and_tables_mock.assert_called_once_with()


def test_reset_db_and_tables_raises_for_unsupported_driver() -> None:
    # Arrange
    expected_settings = SimpleNamespace(effective_database_url="mysql://user:pass@localhost:3306/learnwithai")

    # Act / Assert
    with (
        patch("learnwithai.db.get_settings", return_value=expected_settings),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
    ):
        try:
            db.reset_db_and_tables()
        except ValueError as exc:
            assert str(exc) == "Unsupported database driver for reset: mysql"
        else:
            raise AssertionError("Expected reset_db_and_tables to raise ValueError")


def test_reset_postgresql_database_recreates_database() -> None:
    # Arrange
    database_url = db.make_url("postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai")
    admin_engine = MagicMock()
    connection = MagicMock()
    admin_engine.connect.return_value.__enter__.return_value = connection

    # Act
    with patch("learnwithai.db.create_engine", return_value=admin_engine) as create_engine_mock:
        db._reset_postgresql_database(database_url)

    # Assert
    create_engine_mock.assert_called_once_with(
        database_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    assert connection.execute.call_count == 3
    terminate_call = connection.execute.call_args_list[0]
    assert terminate_call.args[1] == {"database_name": "learnwithai"}
    admin_engine.dispose.assert_called_once_with()


def test_reset_postgresql_database_raises_without_database_name() -> None:
    # Arrange
    database_url = db.make_url("postgresql+psycopg://postgres:postgres@postgres")

    # Act / Assert
    try:
        db._reset_postgresql_database(database_url)
    except ValueError as exc:
        assert str(exc) == "Database URL must include a database name"
    else:
        raise AssertionError("Expected _reset_postgresql_database to raise ValueError")


def test_quote_identifier_escapes_quotes() -> None:
    # Arrange / Act
    quoted = db._quote_identifier('learn"withai')

    # Assert
    assert quoted == '"learn""withai"'


def test_get_session_yields_session_from_engine() -> None:
    # Arrange
    expected_engine = object()
    mock_session = MagicMock()

    # Act
    with (
        patch("learnwithai.db.get_engine", return_value=expected_engine),
        patch("learnwithai.db.Session", return_value=mock_session) as session_mock,
    ):
        gen = db.get_session()
        yielded = next(gen)

    # Assert
    assert yielded is mock_session
    session_mock.assert_called_once_with(expected_engine)


def test_get_session_commits_and_closes_on_success() -> None:
    # Arrange
    mock_session = MagicMock()

    # Act
    with (
        patch("learnwithai.db.get_engine"),
        patch("learnwithai.db.Session", return_value=mock_session),
    ):
        gen = db.get_session()
        next(gen)
        try:
            next(gen)
        except StopIteration:
            pass

    # Assert
    mock_session.commit.assert_called_once_with()
    mock_session.close.assert_called_once_with()
    mock_session.rollback.assert_not_called()


def test_get_session_runs_after_commit_callbacks_after_commit() -> None:
    # Arrange
    mock_session = MagicMock()
    mock_session.info = {}
    call_order: list[str] = []
    mock_session.commit.side_effect = lambda: call_order.append("commit")

    # Act
    with (
        patch("learnwithai.db.get_engine"),
        patch("learnwithai.db.Session", return_value=mock_session),
    ):
        gen = db.get_session()
        yielded = next(gen)
        db.add_after_commit_callback(yielded, lambda: call_order.append("callback"))
        try:
            next(gen)
        except StopIteration:
            pass

    # Assert
    assert call_order == ["commit", "callback"]
    assert mock_session.info == {}


def test_get_session_rolls_back_and_closes_on_exception() -> None:
    # Arrange
    mock_session = MagicMock()

    # Act
    with (
        patch("learnwithai.db.get_engine"),
        patch("learnwithai.db.Session", return_value=mock_session),
    ):
        gen = db.get_session()
        next(gen)
        try:
            gen.throw(ValueError("db error"))
        except ValueError:
            pass

    # Assert
    mock_session.rollback.assert_called_once_with()
    mock_session.close.assert_called_once_with()
    mock_session.commit.assert_not_called()


def test_get_session_discards_after_commit_callbacks_on_exception() -> None:
    # Arrange
    mock_session = MagicMock()
    mock_session.info = {}
    callback = MagicMock()

    # Act
    with (
        patch("learnwithai.db.get_engine"),
        patch("learnwithai.db.Session", return_value=mock_session),
    ):
        gen = db.get_session()
        yielded = next(gen)
        db.add_after_commit_callback(yielded, callback)
        try:
            gen.throw(ValueError("db error"))
        except ValueError:
            pass

    # Assert
    callback.assert_not_called()
    assert mock_session.info == {}
