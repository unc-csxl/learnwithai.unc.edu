from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine

from learnwithai.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(
        settings.effective_database_url,
        echo=settings.db_echo,
    )


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Session:
    return Session(get_engine())
