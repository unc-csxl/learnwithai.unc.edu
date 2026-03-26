"""Database engine and session helpers."""

from collections.abc import Callable, Generator
from functools import lru_cache
from importlib import import_module
from typing import TypeAlias

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlmodel import Session, SQLModel, create_engine

from learnwithai.config import get_settings

AfterCommitCallback: TypeAlias = Callable[[], None]

_AFTER_COMMIT_CALLBACKS_KEY = "after_commit_callbacks"


@lru_cache
def get_engine():
    """Builds and caches the SQLModel engine for the active settings."""
    settings = get_settings()
    return create_engine(
        settings.effective_database_url,
        echo=settings.db_echo,
    )


def create_db_and_tables() -> None:
    """Creates all configured database tables."""
    load_table_metadata()
    SQLModel.metadata.create_all(get_engine())


def load_table_metadata() -> None:
    """Imports SQLModel table modules so their metadata is registered."""
    import_module("learnwithai.tables")


def reset_db_and_tables() -> None:
    """Drops and recreates the configured database, then creates all tables.

    PostgreSQL databases are dropped and recreated from the admin ``postgres``
    database. File-backed SQLite databases are deleted and rebuilt. In-memory
    SQLite databases are reset by dropping and recreating tables.

    Raises:
        ValueError: If the configured database driver is unsupported or the
            database URL does not include a database name.
    """
    engine = get_engine()
    database_url = make_url(get_settings().effective_database_url)

    if database_url.drivername.startswith("postgresql"):
        engine.dispose()
        _reset_postgresql_database(database_url)
    else:
        raise ValueError(f"Unsupported database driver for reset: {database_url.drivername}")

    get_engine.cache_clear()
    create_db_and_tables()


def _reset_postgresql_database(database_url: URL) -> None:
    """Drops and recreates a PostgreSQL database.

    Args:
        database_url: Database URL for the target database.

    Raises:
        ValueError: If the URL does not include a database name.
    """
    database_name = database_url.database
    if not database_name:
        raise ValueError("Database URL must include a database name")

    admin_url = database_url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    quoted_database_name = _quote_identifier(database_name)

    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :database_name "
                    "AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f"DROP DATABASE IF EXISTS {quoted_database_name}"))
            connection.execute(text(f"CREATE DATABASE {quoted_database_name}"))
    finally:
        admin_engine.dispose()


def _quote_identifier(identifier: str) -> str:
    """Safely quotes a SQL identifier for PostgreSQL statements.

    Args:
        identifier: Identifier to quote.

    Returns:
        The quoted identifier.
    """
    return '"' + identifier.replace('"', '""') + '"'


def add_after_commit_callback(session: Session, callback: AfterCommitCallback) -> None:
    """Registers a callback to run after a successful session commit.

    Args:
        session: Open transactional session.
        callback: Zero-argument callable to run after commit succeeds.
    """
    callbacks = session.info.setdefault(_AFTER_COMMIT_CALLBACKS_KEY, [])
    callbacks.append(callback)


def _run_after_commit_callbacks(session: Session) -> None:
    """Runs and clears any callbacks registered for post-commit work.

    Args:
        session: Session whose queued callbacks should be executed.
    """
    callbacks = list(session.info.pop(_AFTER_COMMIT_CALLBACKS_KEY, []))
    for callback in callbacks:
        callback()


def _clear_after_commit_callbacks(session: Session) -> None:
    """Drops any queued post-commit callbacks without executing them.

    Args:
        session: Session whose queued callbacks should be discarded.
    """
    session.info.pop(_AFTER_COMMIT_CALLBACKS_KEY, None)


def get_session() -> Generator[Session, None, None]:
    """Yield a transactional session; commits on success, rolls back on error.

    The session commits when the route handler returns normally.
    Any unhandled exception triggers a rollback before propagating.
    The connection is always released in the finally block.
    """
    session = Session(get_engine())
    try:
        yield session
        session.commit()
        _run_after_commit_callbacks(session)
    except Exception:
        session.rollback()
        _clear_after_commit_callbacks(session)
        raise
    finally:
        session.close()
