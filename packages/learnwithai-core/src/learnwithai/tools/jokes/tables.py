"""Database-backed joke request table."""

from datetime import datetime
from typing import Any

from sqlalchemy.types import JSON
from sqlmodel import (
    Column,
    DateTime,
    Field,
    ForeignKey,
    Integer,
    SQLModel,
    Text,
    func,
)


class JokeRequest(SQLModel, table=True):
    """First-class table for joke generation requests.

    Stores the user-facing prompt and generated jokes. The async job
    lifecycle (status, timing) is tracked by the linked ``AsyncJob``
    row.
    """

    __tablename__ = "joke_request"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    created_by_pid: int = Field(
        sa_column=Column(Integer, nullable=False),
    )
    prompt: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    jokes: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )
    async_job_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("async_job.id"), nullable=True),
    )
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
