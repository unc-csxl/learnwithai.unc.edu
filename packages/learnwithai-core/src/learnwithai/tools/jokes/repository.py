"""Persistence helpers for joke records."""

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from .tables import Joke


class JokeRepository:
    """Provides CRUD operations for joke records."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write joke records.
        """
        self._session = session

    def create(self, joke: Joke) -> Joke:
        """Persists a new joke.

        Args:
            joke: Instance to insert.

        Returns:
            The persisted joke with refreshed database state.
        """
        self._session.add(joke)
        self._session.flush()
        self._session.refresh(joke)
        return joke

    def get_by_id(self, joke_id: int) -> Joke | None:
        """Looks up a joke by its primary key.

        Args:
            joke_id: Primary key of the joke.

        Returns:
            The matching joke when found; otherwise, ``None``.
        """
        return self._session.get(Joke, joke_id)

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

    def update(self, joke: Joke) -> Joke:
        """Persists changes to an existing joke.

        Args:
            joke: Instance with updated fields.

        Returns:
            The updated joke with refreshed database state.
        """
        self._session.add(joke)
        self._session.flush()
        self._session.refresh(joke)
        return joke

    def delete(self, joke: Joke) -> None:
        """Removes a joke from the database.

        Args:
            joke: Instance to delete.
        """
        self._session.delete(joke)
        self._session.flush()
