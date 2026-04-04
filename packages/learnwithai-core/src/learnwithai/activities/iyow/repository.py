"""Persistence helpers for IYOW activity and submission records."""

from sqlalchemy.orm import contains_eager, joinedload
from sqlmodel import col, select

from ...repositories.base_repository import BaseRepository
from ...tables.submission import Submission
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

    def list_active_for_activity(self, activity_id: int) -> list[IyowSubmission]:
        """Returns active IYOW submissions for an activity.

        Args:
            activity_id: Primary key of the activity whose active submissions
                should be loaded.

        Returns:
            Matching IYOW submission details ordered by submission time
            descending. Each detail includes its base submission and linked
            async job loaded eagerly.
        """
        stmt = (
            select(IyowSubmission)
            .join(Submission, col(IyowSubmission.submission_id) == col(Submission.id))
            .options(
                contains_eager(IyowSubmission.submission),  # type: ignore[arg-type]
                joinedload(IyowSubmission.async_job),  # type: ignore[arg-type]
            )
            .where(col(Submission.activity_id) == activity_id, col(Submission.is_active))
            .order_by(col(Submission.submitted_at).desc())
        )
        return list(self._session.exec(stmt).all())

    def get_by_async_job_id(self, async_job_id: int) -> IyowSubmission | None:
        """Looks up an IYOW submission by its linked async job ID.

        Args:
            async_job_id: Primary key of the linked async job.

        Returns:
            The matching IYOW submission when found; otherwise, ``None``.
        """
        stmt = select(IyowSubmission).where(IyowSubmission.async_job_id == async_job_id)
        return self._session.exec(stmt).first()
