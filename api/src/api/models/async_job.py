# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Shared Pydantic models for async job API responses."""

from datetime import datetime

from learnwithai.tables.async_job import AsyncJobStatus
from pydantic import BaseModel


class AsyncJobInfo(BaseModel):
    """Nested representation of an async job's current state.

    Designed for embedding inside feature-specific response models so
    that job lifecycle fields (status, timing) are grouped together
    rather than flattened alongside domain data.
    """

    id: int
    status: AsyncJobStatus
    completed_at: datetime | None
