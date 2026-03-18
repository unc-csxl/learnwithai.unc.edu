"""Persistence helpers for membership (user-course join) records."""

from ..db import Session
from ..tables.membership import Membership
from sqlmodel import select, col


class MembershipRepository:
    """Provides membership lookup and persistence operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write membership records.
        """
        self._session = session

    def create(self, membership: Membership) -> Membership:
        """Persists a new membership and reloads database defaults.

        Args:
            membership: Membership instance to insert.

        Returns:
            The persisted membership with refreshed database state.
        """
        self._session.add(membership)
        self._session.flush()
        self._session.refresh(membership)
        return membership

    def get_by_id(self, membership_id: int) -> Membership | None:
        """Looks up a membership by primary key.

        Args:
            membership_id: Membership identifier.

        Returns:
            The matching membership when found; otherwise, ``None``.
        """
        query = select(Membership).where(col(Membership.id) == membership_id)
        return self._session.exec(query).one_or_none()

    def get_by_user_and_course(
        self, user_pid: int, course_id: int
    ) -> Membership | None:
        """Looks up a membership by user PID and course ID.

        Args:
            user_pid: UNC person identifier.
            course_id: Course identifier.

        Returns:
            The matching membership when found; otherwise, ``None``.
        """
        query = select(Membership).where(
            col(Membership.user_pid) == user_pid,
            col(Membership.course_id) == course_id,
        )
        return self._session.exec(query).one_or_none()

    def update(self, membership: Membership) -> Membership:
        """Merges changes to an existing membership and refreshes state.

        Args:
            membership: Membership instance with updated fields.

        Returns:
            The updated membership with refreshed database state.
        """
        merged = self._session.merge(membership)
        self._session.flush()
        self._session.refresh(merged)
        return merged

    def delete(self, membership_id: int) -> None:
        """Deletes a membership by primary key.

        Args:
            membership_id: Identifier of the membership to remove.
        """
        membership = self.get_by_id(membership_id)
        if membership is not None:
            self._session.delete(membership)
            self._session.flush()
