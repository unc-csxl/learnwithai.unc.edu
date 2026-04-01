"""Database-backed submission models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, func
from sqlmodel import Boolean, Field, SQLModel


class Submission(SQLModel, table=True):
    """Represents a student submission to an activity.

    This is the shared base table for all submission types. Each
    activity type stores additional detail in its own submission table
    linked via ``submission_id``.

    The partial unique index enforces at most one active submission
    per student per activity.
    """

    __table_args__ = (
        Index("ix_submission_activity_id", "activity_id"),
        Index("ix_submission_student", "activity_id", "student_pid"),
        Index(
            "uq_submission_active",
            "activity_id",
            "student_pid",
            unique=True,
            postgresql_where=Column("is_active") == True,  # noqa: E712
        ),
    )

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    activity_id: int = Field(
        sa_column=Column(Integer, ForeignKey("activity.id"), nullable=False),
    )
    student_pid: int = Field(
        sa_column=Column(Integer, ForeignKey("user.pid"), nullable=False),
    )
    is_active: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default="true"),
    )
    max_points: float | None = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
    )
    points: float | None = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
    )
    submitted_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        default=None,
    )
