"""Database-backed membership (user-course join) models."""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, func
from sqlmodel import Field, SQLModel


class MembershipType(str, enum.Enum):
    """Role a user holds within a course."""

    INSTRUCTOR = "instructor"
    TA = "ta"
    STUDENT = "student"


class MembershipState(str, enum.Enum):
    """Lifecycle state of a course membership."""

    ENROLLED = "enrolled"
    DROPPED = "dropped"


class Membership(SQLModel, table=True):
    """Join table linking users to courses with role and state."""

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    user_pid: int = Field(
        sa_column=Column(Integer, ForeignKey("user.pid"), nullable=False),
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), nullable=False),
    )
    type: MembershipType = Field(
        sa_column=Column(
            Enum(MembershipType, values_callable=lambda e: [m.value for m in e]),
            nullable=False,
        ),
    )
    state: MembershipState = Field(
        sa_column=Column(
            Enum(
                MembershipState,
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            server_default=MembershipState.ENROLLED.value,
        ),
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
