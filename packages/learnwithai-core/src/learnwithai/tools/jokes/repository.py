"""Persistence helpers for joke records."""

from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from ...repositories.base_repository import BaseRepository
from .tables import Joke


class JokeRepository(BaseRepository[Joke, int]):
    """Provides CRUD operations for joke records."""

    @property
    def model_type(self) -> type[Joke]:
        """Returns the SQLModel class managed by this repository."""
        return Joke

    def get_by_async_job_id(self, async_job_id: int) -> Joke | None:
        """Looks up a joke by its linked async job ID.

        Args:
            async_job_id: Primary key of the linked async job.

        Returns:
            The matching joke when found; otherwise, ``None``.
        """
        stmt = select(Joke).where(Joke.async_job_id == async_job_id)
        return self._session.exec(stmt).first()

    def list_by_course(self, course_id: int) -> list[Joke]:
        """Returns all jokes for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of jokes ordered by creation time descending.
        """
        stmt = select(Joke).where(Joke.course_id == course_id).order_by(col(Joke.created_at).desc())
        return list(self._session.exec(stmt).all())

    def list_by_course_with_jobs(self, course_id: int) -> list[Joke]:
        """Returns all jokes for a course with their linked async jobs eagerly loaded.

        Uses eager loading via the ``Joke.async_job`` relationship so
        callers can access ``joke.async_job`` without additional queries.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of jokes ordered by creation time descending, each
            with ``async_job`` pre-loaded (``None`` when no linked job).
        """
        stmt = (
            select(Joke)
            .options(selectinload(Joke.async_job))  # type: ignore[arg-type]
            .where(Joke.course_id == course_id)
            .order_by(col(Joke.created_at).desc())
        )
        return list(self._session.exec(stmt).all())
