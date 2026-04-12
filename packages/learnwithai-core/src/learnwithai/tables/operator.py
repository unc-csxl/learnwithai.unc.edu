# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Database-backed operator models for system administration."""

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
    from .user import User


class OperatorRole(str, enum.Enum):
    """Tier of system access granted to an operator."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    HELPDESK = "helpdesk"


class OperatorPermission(str, enum.Enum):
    """Individual capability that can be checked at authorization boundaries."""

    MANAGE_OPERATORS = "manage_operators"
    VIEW_METRICS = "view_metrics"
    VIEW_JOBS = "view_jobs"
    VIEW_SYSTEM = "view_system"
    IMPERSONATE = "impersonate"


ROLE_PERMISSIONS: dict[OperatorRole, frozenset[OperatorPermission]] = {
    OperatorRole.SUPERADMIN: frozenset(OperatorPermission),
    OperatorRole.ADMIN: frozenset(
        {
            OperatorPermission.MANAGE_OPERATORS,
            OperatorPermission.VIEW_METRICS,
            OperatorPermission.VIEW_JOBS,
            OperatorPermission.VIEW_SYSTEM,
        }
    ),
    OperatorRole.HELPDESK: frozenset(
        {
            OperatorPermission.VIEW_METRICS,
            OperatorPermission.VIEW_JOBS,
        }
    ),
}


def effective_permissions(operator: "Operator") -> frozenset[OperatorPermission]:
    """Returns the effective permission set for an operator.

    Currently this simply looks up the role's fixed permission set.
    The function exists as an abstraction point so that per-operator
    grants and revocations can be layered in later without changing
    call sites.

    Args:
        operator: Operator whose permissions should be resolved.

    Returns:
        The set of permissions the operator currently holds.
    """
    return ROLE_PERMISSIONS[operator.role]


class Operator(SQLModel, table=True):
    """Records that a user is a system operator with a given role."""

    user_pid: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.pid"),
            primary_key=True,
            autoincrement=False,
            nullable=False,
        ),
    )
    role: OperatorRole = Field(
        sa_column=Column(
            Enum(OperatorRole, values_callable=lambda e: [m.value for m in e]),
            nullable=False,
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
    created_by_pid: int | None = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.pid"),
            nullable=True,
        ),
        default=None,
    )

    user: "User" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Operator.user_pid == User.pid",
            "foreign_keys": "[Operator.user_pid]",
            "viewonly": True,
        }
    )
