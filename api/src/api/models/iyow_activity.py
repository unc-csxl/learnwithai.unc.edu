# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Pydantic models for In Your Own Words activity APIs."""

from datetime import datetime

from pydantic import BaseModel

from .activity import StudentRosterIdentity
from .async_job import AsyncJobInfo


class CreateIyowActivityRequest(BaseModel):
    """Request body for creating an In Your Own Words activity."""

    title: str
    prompt: str
    rubric: str
    release_date: datetime
    due_date: datetime
    late_date: datetime | None = None


class UpdateIyowActivityRequest(BaseModel):
    """Request body for updating an In Your Own Words activity."""

    title: str
    prompt: str
    rubric: str
    release_date: datetime
    due_date: datetime
    late_date: datetime | None = None


class IyowActivityResponse(BaseModel):
    """Response for an IYOW activity including type-specific detail."""

    id: int
    course_id: int
    type: str
    title: str
    prompt: str
    rubric: str | None
    release_date: datetime
    due_date: datetime
    late_date: datetime | None
    created_at: datetime


class SubmitIyowRequest(BaseModel):
    """Request body for submitting a student response to an IYOW activity."""

    response_text: str


class IyowSubmissionResponse(BaseModel):
    """Response for a single IYOW submission."""

    id: int
    activity_id: int
    student_pid: int
    is_active: bool
    submitted_at: datetime
    response_text: str
    feedback: str | None
    job: AsyncJobInfo | None


class IyowStudentSubmissionRow(StudentRosterIdentity):
    """One row in the instructor submissions roster view.

    Includes every enrolled student. Students who have not submitted
    have ``None`` for the submission fields.
    """

    submission: IyowSubmissionResponse | None
