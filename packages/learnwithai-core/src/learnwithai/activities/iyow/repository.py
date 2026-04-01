"""Persistence helpers for IYOW activity and submission records."""

from sqlmodel import Session, select

from .tables import IyowActivity, IyowSubmission


class IyowActivityRepository:
    """Provides CRUD operations for IYOW activity detail records."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write IYOW activity records.
        """
        self._session = session

    def create(self, iyow_activity: IyowActivity) -> IyowActivity:
        """Persists a new IYOW activity detail.

        Args:
            iyow_activity: Instance to insert.

        Returns:
            The persisted record with refreshed database state.
        """
        self._session.add(iyow_activity)
        self._session.flush()
        self._session.refresh(iyow_activity)
        return iyow_activity

    def get_by_activity_id(self, activity_id: int) -> IyowActivity | None:
        """Looks up an IYOW activity by its base activity ID.

        Args:
            activity_id: Primary key of the base activity.

        Returns:
            The matching IYOW detail when found; otherwise, ``None``.
        """
        stmt = select(IyowActivity).where(IyowActivity.activity_id == activity_id)
        return self._session.exec(stmt).first()

    def update(self, iyow_activity: IyowActivity) -> IyowActivity:
        """Persists changes to an existing IYOW activity detail.

        Args:
            iyow_activity: Instance with updated fields.

        Returns:
            The updated record with refreshed database state.
        """
        self._session.add(iyow_activity)
        self._session.flush()
        self._session.refresh(iyow_activity)
        return iyow_activity


class IyowSubmissionRepository:
    """Provides CRUD operations for IYOW submission detail records."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write IYOW submission records.
        """
        self._session = session

    def create(self, iyow_submission: IyowSubmission) -> IyowSubmission:
        """Persists a new IYOW submission detail.

        Args:
            iyow_submission: Instance to insert.

        Returns:
            The persisted record with refreshed database state.
        """
        self._session.add(iyow_submission)
        self._session.flush()
        self._session.refresh(iyow_submission)
        return iyow_submission

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

    def update(self, iyow_submission: IyowSubmission) -> IyowSubmission:
        """Persists changes to an existing IYOW submission.

        Args:
            iyow_submission: Instance with updated fields.

        Returns:
            The updated record with refreshed database state.
        """
        self._session.add(iyow_submission)
        self._session.flush()
        self._session.refresh(iyow_submission)
        return iyow_submission
