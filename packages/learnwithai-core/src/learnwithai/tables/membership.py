# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Database-backed membership (user-course join) models."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import (
    Column,
    DateTime,
    Enum,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
    func,
)

if TYPE_CHECKING:
    from .course import Course
    from .user import User


class MembershipType(str, enum.Enum):
    """Role a user holds within a course."""

    INSTRUCTOR = "instructor"
    TA = "ta"
    STUDENT = "student"


class MembershipState(str, enum.Enum):
    """Lifecycle state of a course membership."""

    PENDING = "pending"
    ENROLLED = "enrolled"
    DROPPED = "dropped"


class Membership(SQLModel, table=True):
    """Join table linking users to courses with role and state."""

    user_pid: int = Field(
        sa_column=Column(Integer, primary_key=True, nullable=False),
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id"), primary_key=True, nullable=False),
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
            server_default=MembershipState.PENDING.value,
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
    course: "Course" = Relationship()
    user: "User" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Membership.user_pid == User.pid",
            "foreign_keys": "[Membership.user_pid]",
            "viewonly": True,
        }
    )
