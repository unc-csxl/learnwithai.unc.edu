# This file has been moved to repository.py. Delete this file.
_placeholder = None
    """Provides CRUD operations for joke request records."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write joke request records.
        """
        self._session = session

    def create(self, joke_request: JokeRequest) -> JokeRequest:
        """Persists a new joke request.

        Args:
            joke_request: Instance to insert.

        Returns:
            The persisted joke request with refreshed database state.
        """
        self._session.add(joke_request)
        self._session.flush()
        self._session.refresh(joke_request)
        return joke_request

    def get_by_id(self, joke_request_id: int) -> JokeRequest | None:
        """Looks up a joke request by its primary key.

        Args:
            joke_request_id: Primary key of the joke request.

        Returns:
            The matching joke request when found; otherwise, ``None``.
        """
        return self._session.get(JokeRequest, joke_request_id)

    def get_by_async_job_id(self, async_job_id: int) -> JokeRequest | None:
        """Looks up a joke request by its linked async job ID.

        Args:
            async_job_id: Primary key of the linked async job.

        Returns:
            The matching joke request when found; otherwise, ``None``.
        """
        stmt = select(JokeRequest).where(JokeRequest.async_job_id == async_job_id)
        return self._session.exec(stmt).first()

    def list_by_course(self, course_id: int) -> list[JokeRequest]:
        """Returns all joke requests for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of joke requests ordered by creation time descending.
        """
        stmt = (
            select(JokeRequest).where(JokeRequest.course_id == course_id).order_by(col(JokeRequest.created_at).desc())
        )
        return list(self._session.exec(stmt).all())

    def update(self, joke_request: JokeRequest) -> JokeRequest:
        """Persists changes to an existing joke request.

        Args:
            joke_request: Instance with updated fields.

        Returns:
            The updated joke request with refreshed database state.
        """
        self._session.add(joke_request)
        self._session.flush()
        self._session.refresh(joke_request)
        return joke_request

    def delete(self, joke_request: JokeRequest) -> None:
        """Removes a joke request from the database.

        Args:
            joke_request: Instance to delete.
        """
        self._session.delete(joke_request)
        self._session.flush()
