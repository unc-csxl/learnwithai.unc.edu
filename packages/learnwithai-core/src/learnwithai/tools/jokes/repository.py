"""Persistence helpers for joke records."""

from sqlmodel import Session, col, select

from ...tables.async_job import AsyncJob
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

    def list_by_course_with_jobs(self, course_id: int) -> list[tuple[Joke, AsyncJob | None]]:
        """Returns all jokes for a course with their linked async jobs.

        Uses a single LEFT JOIN to avoid N+1 queries when the caller
        needs both joke data and job status.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of ``(joke, async_job)`` tuples ordered by creation
            time descending.  ``async_job`` is ``None`` when the joke
            has no linked job.
        """
        stmt = (
            select(Joke, AsyncJob)
            .outerjoin(AsyncJob, col(Joke.async_job_id) == col(AsyncJob.id))
            .where(Joke.course_id == course_id)
            .order_by(col(Joke.created_at).desc())
        )
        return [(joke, job) for joke, job in self._session.exec(stmt).all()]

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
