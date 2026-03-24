"""Database-backed course models."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Integer, func
from sqlmodel import Field, SQLModel


class Term(StrEnum):
    """Academic term within a year."""

    FALL = "fall"
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"


class Course(SQLModel, table=True):
    """Represents a course offered in the system."""

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    course_number: str = Field()
    name: str = Field()
    description: str = Field(default="")
    term: Term = Field()
    year: int = Field()
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
