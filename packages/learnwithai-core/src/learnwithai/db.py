"""Database engine and session helpers."""

from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine

from learnwithai.config import get_settings


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
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Session:
    """Creates a new SQLModel session bound to the shared engine."""
    return Session(get_engine())
