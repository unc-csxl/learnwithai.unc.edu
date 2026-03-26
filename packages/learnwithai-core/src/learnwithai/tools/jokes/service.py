"""Service layer for joke generation CRUD operations."""

from ...interfaces import JobQueue
from ...repositories.async_job_repository import AsyncJobRepository
from ...repositories.joke_request_repository import JokeRequestRepository
from ...tables.async_job import AsyncJob, AsyncJobStatus
from ...tables.user import User
from .models import JOKE_GENERATION_KIND, JokeGenerationJob
from .tables import JokeRequest


class JokeGenerationService:
    """Orchestrates creation, listing, retrieval, and deletion of joke requests."""

    def __init__(
        self,
        joke_request_repo: JokeRequestRepository,
        async_job_repo: AsyncJobRepository,
        job_queue: JobQueue,
    ):
        """Initializes the service with its dependencies.

        Args:
            joke_request_repo: Repository for joke request records.
            async_job_repo: Repository for unified async job records.
            job_queue: Queue used to dispatch background jobs.
        """
        self._joke_request_repo = joke_request_repo
        self._async_job_repo = async_job_repo
        self._job_queue = job_queue

    def create_request(self, subject: User, course_id: int, prompt: str) -> JokeRequest:
        """Creates a joke request, its async job, and enqueues it.

        Args:
            subject: The authenticated instructor submitting the request.
            course_id: Primary key of the course.
            prompt: Description of the topic to generate jokes about.

        Returns:
            The persisted joke request with a linked PENDING async job.
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

        joke_request = self._joke_request_repo.create(
            JokeRequest(
                course_id=course_id,
                created_by_pid=subject.pid,
                prompt=prompt,
                async_job_id=async_job.id,
            )
        )

        self._job_queue.enqueue(JokeGenerationJob(job_id=async_job.id))
        return joke_request

    def list_requests(self, course_id: int) -> list[JokeRequest]:
        """Returns all joke requests for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of joke requests ordered by creation time descending.
        """
        return self._joke_request_repo.list_by_course(course_id)

    def get_request(self, joke_request_id: int) -> JokeRequest | None:
        """Returns a single joke request by ID.

        Args:
            joke_request_id: Primary key of the joke request.

        Returns:
            The matching joke request, or ``None`` if not found.
        """
        return self._joke_request_repo.get_by_id(joke_request_id)

    def delete_request(self, joke_request_id: int) -> None:
        """Deletes a joke request and its linked async job.

        Args:
            joke_request_id: Primary key of the joke request to delete.

        Raises:
            ValueError: If the joke request does not exist.
        """
        joke_request = self._joke_request_repo.get_by_id(joke_request_id)
        if joke_request is None:
            raise ValueError(f"JokeRequest {joke_request_id} not found")
        if joke_request.async_job_id is not None:
            async_job = self._async_job_repo.get_by_id(joke_request.async_job_id)
            if async_job is not None:
                self._async_job_repo.delete(async_job)
        self._joke_request_repo.delete(joke_request)
