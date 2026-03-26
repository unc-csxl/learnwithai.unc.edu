"""Database-backed joke table for the joke generation tool."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.types import JSON
from sqlmodel import (
    Column,
    DateTime,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
    Text,
    func,
)

from ...tables.async_job import AsyncJob  # noqa: F401 — registered for relationship resolution


class Joke(SQLModel, table=True):
    """First-class table for joke generation results.

    Stores the user-facing prompt and generated jokes. The async job
    lifecycle (status, timing) is tracked by the linked ``AsyncJob``
    row, accessible via the ``async_job`` relationship.
    """

    __tablename__: str = "joke_tool__joke"  # type: ignore[assignment]

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    created_by_pid: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.pid"), nullable=True),
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
    async_job: Optional["AsyncJob"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Joke.async_job_id]", "lazy": "select"},
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
