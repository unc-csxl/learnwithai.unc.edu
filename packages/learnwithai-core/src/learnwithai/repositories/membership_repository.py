"""Persistence helpers for membership (user-course join) records."""

from ..db import Session
from ..tables.membership import Membership


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

    def get_by_user_and_course(
        self, user_pid: int, course_id: int
    ) -> Membership | None:
        """Looks up a membership by its composite primary key.

        Args:
            user_pid: UNC person identifier.
            course_id: Course identifier.

        Returns:
            The matching membership when found; otherwise, ``None``.
        """
        return self._session.get(Membership, (user_pid, course_id))

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

    def delete(self, membership: Membership) -> None:
        """Deletes a membership.

        Args:
            membership: Membership instance to remove.
        """
        self._session.delete(membership)
        self._session.flush()
