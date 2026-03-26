"""Pydantic models for joke generation API requests and responses."""

from datetime import datetime

from learnwithai.tables.async_job import AsyncJobStatus
from pydantic import BaseModel


class CreateJokeRequest(BaseModel):
    """Request body for submitting a joke generation request."""

    prompt: str


class JokeRequestResponse(BaseModel):
    """Response for a single joke generation job."""

    id: int
    status: AsyncJobStatus
    prompt: str
    jokes: list[str]
    created_at: datetime
    completed_at: datetime | None
