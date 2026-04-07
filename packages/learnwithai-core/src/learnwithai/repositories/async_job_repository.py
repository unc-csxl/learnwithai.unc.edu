# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Persistence helpers for unified async job records."""

from sqlmodel import select

from ..tables.async_job import AsyncJob
from .base_repository import BaseRepository


class AsyncJobRepository(BaseRepository[AsyncJob, int]):
    """Provides CRUD operations for async background jobs."""

    @property
    def model_type(self) -> type[AsyncJob]:
        """Returns the SQLModel class managed by this repository."""
        return AsyncJob

    def list_by_course_and_kind(self, course_id: int, kind: str) -> list[AsyncJob]:
        """Returns all jobs for a specific course and kind.

        Args:
            course_id: The course to filter by.
            kind: The job kind to filter by.

        Returns:
            A list of jobs ordered by creation time descending.
        """
        stmt = (
            select(AsyncJob)
            .where(AsyncJob.course_id == course_id)
            .where(AsyncJob.kind == kind)
            .order_by(AsyncJob.created_at.desc())  # type: ignore[union-attr]
        )
        return list(self._session.exec(stmt).all())
