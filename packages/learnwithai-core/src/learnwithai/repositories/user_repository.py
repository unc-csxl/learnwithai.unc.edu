"""Persistence helpers for user records."""

from sqlmodel import select

from ..tables.user import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User, int]):
    """Provides user lookup and persistence operations."""

    @property
    def model_type(self) -> type[User]:
        """Returns the SQLModel class managed by this repository."""
        return User

    def get_by_pid(self, pid: int) -> User | None:
        """Looks up a user by PID (primary key).

        Args:
            pid: UNC person identifier.

        Returns:
            The matching user when found; otherwise, ``None``.
        """
        return self.get_by_id(pid)

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
        return self.create(new_user)

    def update_user(self, user: User) -> User:
        """Persists changes to an existing user and refreshes state.

        Args:
            user: User instance with updated fields.

        Returns:
            The updated user with refreshed database state.
        """
        return self.update(user)
