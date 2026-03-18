"""Persistence helpers for user records."""

from ..db import Session
from ..tables.user import User


class UserRepository:
    """Provides user lookup and persistence operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write user records.
        """
        self._session = session

    def get_by_pid(self, pid: int) -> User | None:
        """Looks up a user by PID (primary key).

        Args:
            pid: UNC person identifier.

        Returns:
            The matching user when found; otherwise, ``None``.
        """
        return self._session.get(User, pid)

    def register_user(self, new_user: User) -> User:
        """Persists a new user record and reloads database defaults.

        Args:
            new_user: User instance to insert.

        Returns:
            The persisted user with refreshed database state.
        """
        self._session.add(new_user)
        self._session.flush()
        self._session.refresh(new_user)
        return new_user
