"""Database-backed activity models."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class ActivityType(StrEnum):
    """Discriminator for activity types."""

    IYOW = "iyow"


class Activity(SQLModel, table=True):
    """Represents an assigned activity within a course.

    This is the shared base table for all activity types. Each type
    stores additional detail in its own table linked via ``activity_id``.
    """

    __table_args__ = (Index("ix_activity_course_id_type", "course_id", "type"),)

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    created_by_pid: int = Field(
        sa_column=Column(Integer, ForeignKey("user.pid"), nullable=False),
    )
    type: ActivityType = Field(
        sa_column=Column(String(32), nullable=False),
    )
    title: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    release_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    due_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    late_date: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
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
