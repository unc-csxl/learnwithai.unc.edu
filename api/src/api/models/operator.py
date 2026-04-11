# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Public API models for system operator management."""

from datetime import datetime

from learnwithai.tables.operator import OperatorPermission, OperatorRole
from pydantic import BaseModel, ConfigDict


class OperatorProfile(BaseModel):
    """Operator summary included in the authenticated user profile."""

    model_config = ConfigDict(from_attributes=True)

    role: OperatorRole
    permissions: list[OperatorPermission]


class OperatorResponse(BaseModel):
    """Detailed operator record returned by admin endpoints."""

    model_config = ConfigDict(from_attributes=True)

    user_pid: int
    user_name: str
    user_email: str | None
    role: OperatorRole
    permissions: list[OperatorPermission]
    created_at: datetime
    created_by_pid: int | None


class GrantOperatorRequest(BaseModel):
    """Payload for granting operator access to a user."""

    user_pid: int
    role: OperatorRole


class UpdateOperatorRoleRequest(BaseModel):
    """Payload for changing an operator's role."""

    role: OperatorRole


class ImpersonationTokenResponse(BaseModel):
    """JWT token issued for user impersonation."""

    token: str


class UserSearchResult(BaseModel):
    """Minimal user record returned by user search."""

    model_config = ConfigDict(from_attributes=True)

    pid: int
    name: str
    email: str | None
