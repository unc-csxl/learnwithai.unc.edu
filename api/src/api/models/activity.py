"""Pydantic models for activity API requests and responses."""

from datetime import datetime

from pydantic import BaseModel

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
