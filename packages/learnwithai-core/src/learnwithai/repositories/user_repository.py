"""Persistence helpers for user records."""

from sqlmodel import select

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

    def list_all(self) -> list[User]:
        """Returns all registered users.

        Returns:
            A list of all user records.
        """
        return list(self._session.exec(select(User)).all())

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

    def update_user(self, user: User) -> User:
        """Merges changes to an existing user and refreshes state.

        Args:
            user: User instance with updated fields.

        Returns:
            The updated user with refreshed database state.
        """
        merged = self._session.merge(user)
        self._session.flush()
        self._session.refresh(merged)
        return merged
