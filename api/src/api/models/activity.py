# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Pydantic models for activity API requests and responses."""

from datetime import datetime

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    """Response for a single activity (shared fields only)."""

    id: int
    course_id: int
    type: str
    title: str
    release_date: datetime
    due_date: datetime
    late_date: datetime | None
    created_at: datetime
    active_submission_count: int | None = None


class StudentRosterIdentity(BaseModel):
    """Shared student identity fields for submission roster rows."""

    student_pid: int
    given_name: str | None
    family_name: str | None
    email: str | None
