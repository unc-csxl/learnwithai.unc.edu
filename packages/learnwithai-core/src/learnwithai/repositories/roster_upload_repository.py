"""Persistence helpers for roster upload job records."""

from sqlmodel import select

from ..db import Session
from ..tables.roster_upload_job import RosterUploadJob


class RosterUploadRepository:
    """Provides CRUD operations for roster CSV upload jobs."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write upload job records.
        """
        self._session = session

    def create(self, job: RosterUploadJob) -> RosterUploadJob:
        """Persists a new roster upload job.

        Args:
            job: Job instance to insert.

        Returns:
            The persisted job with refreshed database state.
        """
        self._session.add(job)
        self._session.flush()
        self._session.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> RosterUploadJob | None:
        """Looks up a roster upload job by its primary key.

        Args:
            job_id: Primary key of the job.

        Returns:
            The matching job when found; otherwise, ``None``.
        """
        return self._session.get(RosterUploadJob, job_id)

    def list_by_course(self, course_id: int) -> list[RosterUploadJob]:
        """Returns all upload jobs for a specific course.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of upload jobs ordered by creation time descending.
        """
        stmt = (
            select(RosterUploadJob)
            .where(RosterUploadJob.course_id == course_id)
            .order_by(RosterUploadJob.created_at.desc())  # type: ignore[union-attr]
        )
        return list(self._session.exec(stmt).all())

    def update(self, job: RosterUploadJob) -> RosterUploadJob:
        """Persists changes to an existing roster upload job.

        Args:
            job: Job instance with updated fields.

        Returns:
            The updated job with refreshed database state.
        """
        self._session.add(job)
        self._session.flush()
        self._session.refresh(job)
        return job
