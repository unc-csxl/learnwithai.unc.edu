# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Persistence helpers for operator records."""

from sqlalchemy.orm import selectinload
from sqlmodel import select

from ..tables.operator import Operator
from .base_repository import BaseRepository


class OperatorRepository(BaseRepository[Operator, int]):
    """Provides operator lookup and persistence operations."""

    @property
    def model_type(self) -> type[Operator]:
        """Returns the SQLModel class managed by this repository."""
        return Operator

    def get_by_user_pid(self, pid: int) -> Operator | None:
        """Looks up an operator record by user PID.

        Args:
            pid: UNC person identifier.

        Returns:
            The matching operator when found; otherwise, ``None``.
        """
        return self.get_by_id(pid)

    def list_all(self) -> list[Operator]:
        """Returns all operator records with user data eagerly loaded.

        Returns:
            A list of all operator records.
        """
        query = select(Operator).options(selectinload(Operator.user))  # type: ignore[arg-type]
        return list(self._session.exec(query).all())
