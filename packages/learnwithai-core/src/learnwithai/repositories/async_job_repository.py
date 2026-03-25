"""Persistence helpers for unified async job records."""

from sqlmodel import select

from ..db import Session
from ..tables.async_job import AsyncJob


class AsyncJobRepository:
    """Provides CRUD operations for async background jobs."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write async job records.
        """
        self._session = session

    def create(self, job: AsyncJob) -> AsyncJob:
        """Persists a new async job.

        Args:
            job: Job instance to insert.

        Returns:
            The persisted job with refreshed database state.
        """
        self._session.add(job)
        self._session.flush()
        self._session.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> AsyncJob | None:
        """Looks up an async job by its primary key.

        Args:
            job_id: Primary key of the job.

        Returns:
            The matching job when found; otherwise, ``None``.
        """
        return self._session.get(AsyncJob, job_id)

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

    def update(self, job: AsyncJob) -> AsyncJob:
        """Persists changes to an existing async job.

        Args:
            job: Job instance with updated fields.

        Returns:
            The updated job with refreshed database state.
        """
        self._session.add(job)
        self._session.flush()
        self._session.refresh(job)
        return job

    def delete(self, job: AsyncJob) -> None:
        """Removes an async job from the database.

        Args:
            job: Job instance to delete.
        """
        self._session.delete(job)
        self._session.flush()
