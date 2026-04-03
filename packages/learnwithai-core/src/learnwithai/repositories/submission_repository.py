"""Persistence helpers for submission records."""

from sqlmodel import col, func, select, update

from ..db import Session
from ..tables.submission import Submission


class SubmissionRepository:
    """Provides submission lookup and persistence operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write submission records.
        """
        self._session = session

    def create(self, submission: Submission) -> Submission:
        """Persists a new submission and reloads database defaults.

        Args:
            submission: Submission instance to insert.

        Returns:
            The persisted submission with refreshed database state.
        """
        self._session.add(submission)
        self._session.flush()
        self._session.refresh(submission)
        return submission

    def get_by_id(self, submission_id: int) -> Submission | None:
        """Looks up a submission by primary key.

        Args:
            submission_id: Submission identifier.

        Returns:
            The matching submission when found; otherwise, ``None``.
        """
        return self._session.get(Submission, submission_id)

    def get_active_for_student(self, activity_id: int, student_pid: int) -> Submission | None:
        """Returns the active submission for a student on an activity.

        Args:
            activity_id: The activity to look up.
            student_pid: PID of the student.

        Returns:
            The active submission when one exists; otherwise, ``None``.
        """
        stmt = select(Submission).where(
            Submission.activity_id == activity_id,
            Submission.student_pid == student_pid,
            Submission.is_active == True,  # noqa: E712
        )
        return self._session.exec(stmt).first()

    def list_by_activity(self, activity_id: int) -> list[Submission]:
        """Returns all active submissions for an activity.

        Args:
            activity_id: The activity to filter by.

        Returns:
            A list of active submissions ordered by submission time descending.
        """
        stmt = (
            select(Submission)
            .where(
                Submission.activity_id == activity_id,
                Submission.is_active == True,  # noqa: E712
            )
            .order_by(col(Submission.submitted_at).desc())
        )
        return list(self._session.exec(stmt).all())

    def list_by_student_and_activity(self, activity_id: int, student_pid: int) -> list[Submission]:
        """Returns all submissions (active and inactive) for a student on an activity.

        Args:
            activity_id: The activity to filter by.
            student_pid: PID of the student.

        Returns:
            A list of submissions ordered by submission time descending.
        """
        stmt = (
            select(Submission)
            .where(
                Submission.activity_id == activity_id,
                Submission.student_pid == student_pid,
            )
            .order_by(col(Submission.submitted_at).desc())
        )
        return list(self._session.exec(stmt).all())

    def deactivate_active(self, activity_id: int, student_pid: int) -> None:
        """Marks the current active submission as inactive.

        This is called before creating a new submission to ensure only
        one submission is active at a time.

        Args:
            activity_id: The activity whose submission to deactivate.
            student_pid: PID of the student.
        """
        stmt = (
            update(Submission)
            .where(
                col(Submission.activity_id) == activity_id,
                col(Submission.student_pid) == student_pid,
                col(Submission.is_active) == True,  # noqa: E712
            )
            .values(is_active=False)
        )
        self._session.exec(stmt)  # type: ignore[call-overload]

    def count_active_by_activity(self, activity_id: int) -> int:
        """Returns the count of active submissions for an activity.

        Args:
            activity_id: The activity to count for.

        Returns:
            The number of active submissions.
        """
        stmt = (
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.activity_id == activity_id,
                Submission.is_active == True,  # noqa: E712
            )
        )
        result = self._session.exec(stmt).one()
        return int(result)

    def update(self, submission: Submission) -> Submission:
        """Merges changes to an existing submission and refreshes state.

        Args:
            submission: Submission instance with updated fields.

        Returns:
            The updated submission with refreshed database state.
        """
        self._session.add(submission)
        self._session.flush()
        self._session.refresh(submission)
        return submission
