"""Database-backed tables for the In Your Own Words activity type."""

from datetime import datetime
from typing import Optional

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
from ...tables.submission import Submission  # noqa: F401 — registered for relationship resolution


class IyowActivity(SQLModel, table=True):
    """Stores the prompt and rubric for an In Your Own Words activity.

    Linked 1:1 with a base :class:`~learnwithai.tables.activity.Activity`
    row via ``activity_id``.
    """

    __tablename__: str = "iyow_activity"  # type: ignore[assignment]

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    activity_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("activity.id"),
            unique=True,
            nullable=False,
        ),
    )
    prompt: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    rubric: str = Field(
        sa_column=Column(Text, nullable=False),
    )


class IyowSubmission(SQLModel, table=True):
    """Stores a student's response and LLM feedback for an IYOW activity.

    Linked 1:1 with a base :class:`~learnwithai.tables.submission.Submission`
    row via ``submission_id``. The ``feedback`` column is ``NULL`` until the
    background job completes.
    """

    __tablename__: str = "iyow_submission"  # type: ignore[assignment]

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    submission_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("submission.id"),
            unique=True,
            nullable=False,
        ),
    )
    response_text: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    feedback: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    async_job_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("async_job.id"), nullable=True),
    )
    async_job: Optional["AsyncJob"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[IyowSubmission.async_job_id]",
            "lazy": "select",
            "cascade": "all, delete",
            "single_parent": True,
        },
    )
    submission: Optional["Submission"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "IyowSubmission.submission_id == Submission.id",
            "foreign_keys": "[IyowSubmission.submission_id]",
            "lazy": "select",
            "viewonly": True,
            "uselist": False,
        },
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        default=None,
    )
