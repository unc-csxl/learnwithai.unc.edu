"""Service layer for joke generation CRUD operations."""

from ...interfaces import JobQueue
from ...repositories.async_job_repository import AsyncJobRepository
from ...tables.async_job import AsyncJob, AsyncJobStatus
from ...tables.user import User
from .models import JOKE_GENERATION_KIND, JokeGenerationJob
from .repository import JokeRepository
from .tables import Joke


class JokeGenerationService:
    """Orchestrates creation, listing, retrieval, and deletion of jokes."""

    def __init__(
        self,
        joke_repo: JokeRepository,
        async_job_repo: AsyncJobRepository,
        job_queue: JobQueue,
    ):
        """Initializes the service with its dependencies.

        Args:
            joke_repo: Repository for joke records.
            async_job_repo: Repository for unified async job records.
            job_queue: Queue used to dispatch background jobs.
        """
        self._joke_repo = joke_repo
        self._async_job_repo = async_job_repo
        self._job_queue = job_queue

    def create(self, subject: User, course_id: int, prompt: str) -> Joke:
        """Creates a joke, its async job, and enqueues it.

        Args:
            subject: The authenticated instructor submitting the request.
            course_id: Primary key of the course.
            prompt: Description of the topic to generate jokes about.

        Returns:
            The persisted joke with a linked PENDING async job.
        """
        async_job = self._async_job_repo.create(
            AsyncJob(
                course_id=course_id,
                created_by_pid=subject.pid,
                kind=JOKE_GENERATION_KIND,
                status=AsyncJobStatus.PENDING,
                input_data={},
            )
        )
        assert async_job.id is not None

        joke = self._joke_repo.create(
            Joke(
                course_id=course_id,
                created_by_pid=subject.pid,
                prompt=prompt,
                async_job_id=async_job.id,
            )
        )

        self._job_queue.enqueue(JokeGenerationJob(job_id=async_job.id))
        return joke

    def list_for_course(self, course_id: int) -> list[Joke]:
        """Returns all jokes for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of jokes ordered by creation time descending.
        """
        return self._joke_repo.list_by_course(course_id)

    def list_for_course_with_jobs(self, course_id: int) -> list[Joke]:
        """Returns all jokes for a course with their async jobs pre-loaded.

        The ``async_job`` relationship is eagerly loaded so callers can
        access ``joke.async_job`` without additional queries.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of jokes ordered by creation time descending.
        """
        return self._joke_repo.list_by_course_with_jobs(course_id)

    def get(self, joke_id: int) -> Joke | None:
        """Returns a single joke by ID.

        Args:
            joke_id: Primary key of the joke.

        Returns:
            The matching joke, or ``None`` if not found.
        """
        return self._joke_repo.get_by_id(joke_id)

    def delete(self, joke_id: int) -> None:
        """Deletes a joke and its linked async job.

        Args:
            joke_id: Primary key of the joke to delete.

        Raises:
            ValueError: If the joke does not exist.
        """
        joke = self._joke_repo.get_by_id(joke_id)
        if joke is None:
            raise ValueError(f"Joke {joke_id} not found")
        self._joke_repo.delete(joke)
