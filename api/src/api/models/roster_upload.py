"""Pydantic models for roster CSV upload API requests and responses."""

from datetime import datetime

from learnwithai.tables.async_job import AsyncJobStatus
from pydantic import BaseModel


class RosterUploadResponse(BaseModel):
    """Response returned when a roster CSV upload is accepted."""

    id: int
    status: AsyncJobStatus


class RosterUploadStatusResponse(BaseModel):
    """Detailed status of a roster upload job."""

    id: int
    status: AsyncJobStatus
    created_count: int
    updated_count: int
    error_count: int
    error_details: str | None
    created_at: datetime
    completed_at: datetime | None
