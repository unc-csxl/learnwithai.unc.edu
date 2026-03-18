"""Database-backed course models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, func
from sqlmodel import Field, SQLModel


class Course(SQLModel, table=True):
    """Represents a course offered in the system."""

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    name: str = Field()
    term: str = Field()
    section: str = Field()
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        default=None,
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
        default=None,
    )
