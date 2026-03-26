"""Pydantic models for joke generation API requests and responses."""

from datetime import datetime

from pydantic import BaseModel

from .async_job import AsyncJobInfo


class CreateJokeRequest(BaseModel):
    """Request body for submitting a joke generation request."""

    prompt: str


class JokeResponse(BaseModel):
    """Response for a single joke generation result."""

    id: int
    prompt: str
    jokes: list[str]
    created_at: datetime
    job: AsyncJobInfo | None
