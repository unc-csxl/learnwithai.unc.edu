"""Persistence helpers for IYOW activity and submission records."""

from sqlmodel import select

from ...repositories.base_repository import BaseRepository
from .tables import IyowActivity, IyowSubmission


class IyowActivityRepository(BaseRepository[IyowActivity, int]):
    """Provides CRUD operations for IYOW activity detail records."""

    @property
    def model_type(self) -> type[IyowActivity]:
        """Returns the SQLModel class managed by this repository."""
        return IyowActivity

    def get_by_activity_id(self, activity_id: int) -> IyowActivity | None:
        """Looks up an IYOW activity by its base activity ID.

        Args:
            activity_id: Primary key of the base activity.

        Returns:
            The matching IYOW detail when found; otherwise, ``None``.
        """
        stmt = select(IyowActivity).where(IyowActivity.activity_id == activity_id)
        return self._session.exec(stmt).first()


class IyowSubmissionRepository(BaseRepository[IyowSubmission, int]):
    """Provides CRUD operations for IYOW submission detail records."""

    @property
    def model_type(self) -> type[IyowSubmission]:
        """Returns the SQLModel class managed by this repository."""
        return IyowSubmission

    def get_by_submission_id(self, submission_id: int) -> IyowSubmission | None:
        """Looks up an IYOW submission by its base submission ID.

        Args:
            submission_id: Primary key of the base submission.

        Returns:
            The matching IYOW detail when found; otherwise, ``None``.
        """
        stmt = select(IyowSubmission).where(IyowSubmission.submission_id == submission_id)
        return self._session.exec(stmt).first()

    def get_by_async_job_id(self, async_job_id: int) -> IyowSubmission | None:
        """Looks up an IYOW submission by its linked async job ID.

        Args:
            async_job_id: Primary key of the linked async job.

        Returns:
            The matching IYOW submission when found; otherwise, ``None``.
        """
        stmt = select(IyowSubmission).where(IyowSubmission.async_job_id == async_job_id)
        return self._session.exec(stmt).first()
