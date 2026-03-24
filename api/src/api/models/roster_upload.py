"""Pydantic models for roster CSV upload API requests and responses."""

from datetime import datetime

from pydantic import BaseModel

from learnwithai.tables.roster_upload_job import RosterUploadStatus


class RosterUploadResponse(BaseModel):
    """Response returned when a roster CSV upload is accepted."""

    id: int
    status: RosterUploadStatus


class RosterUploadStatusResponse(BaseModel):
    """Detailed status of a roster upload job."""

    id: int
    status: RosterUploadStatus
    created_count: int
    updated_count: int
    error_count: int
    error_details: str | None
    created_at: datetime
    completed_at: datetime | None
