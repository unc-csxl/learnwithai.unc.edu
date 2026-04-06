"""Persistence helpers for submission records."""

from sqlmodel import col, func, select, update

from ..tables.activity import Activity
from ..tables.membership import Membership, MembershipState, MembershipType
from ..tables.submission import Submission
from .base_repository import BaseRepository


class SubmissionRepository(BaseRepository[Submission, int]):
    """Provides submission lookup and persistence operations."""

    @property
    def model_type(self) -> type[Submission]:
        """Returns the SQLModel class managed by this repository."""
        return Submission

    def get_active_for_student(self, activity_id: int, student_pid: int) -> Submission | None:
        """Returns the active submission for a student on an activity.

        Args:
            activity_id: The activity to look up.
            student_pid: PID of the student.

        Returns:
            The active submission when one exists; otherwise, ``None``.
        """
        stmt = select(Submission).where(
            col(Submission.activity_id) == activity_id,
            col(Submission.student_pid) == student_pid,
            col(Submission.is_active),
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
            .where(col(Submission.activity_id) == activity_id, col(Submission.is_active))
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
                col(Submission.activity_id) == activity_id,
                col(Submission.student_pid) == student_pid,
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
                col(Submission.is_active),
            )
            .values(is_active=False)
        )
        self._session.exec(stmt)  # type: ignore[call-overload]

    def count_active_by_activity(self, activity_id: int) -> int:
        """Returns the count of active enrolled-student submissions.

        Args:
            activity_id: The activity to count for.

        Returns:
            The number of active submissions from enrolled students in the
            activity's course. Staff preview submissions and inactive
            versions are excluded.
        """
        stmt = (
            select(func.count())
            .select_from(Submission)
            .join(Activity, col(Activity.id) == col(Submission.activity_id))
            .join(
                Membership,
                (col(Membership.user_pid) == col(Submission.student_pid))
                & (col(Membership.course_id) == col(Activity.course_id)),
            )
            .where(
                col(Submission.activity_id) == activity_id,
                col(Submission.is_active),
                col(Membership.type) == MembershipType.STUDENT,
                col(Membership.state) == MembershipState.ENROLLED,
            )
        )
        result = self._session.exec(stmt).one()
        return int(result)
