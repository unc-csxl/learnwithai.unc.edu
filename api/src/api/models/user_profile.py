# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Public API models for authenticated user profile responses."""

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """Represents the authenticated user profile returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    pid: int
    onyen: str
    name: str
    given_name: str
    family_name: str
    email: str


class UpdateProfileRequest(BaseModel):
    """Payload for updating the authenticated user's profile."""

    given_name: str
    family_name: str
