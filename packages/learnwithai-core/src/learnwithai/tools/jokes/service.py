"""Service layer for joke generation job CRUD operations."""

from ...interfaces import JobQueue
from ...repositories.async_job_repository import AsyncJobRepository
from ...tables.async_job import AsyncJob, AsyncJobStatus
from ...tables.user import User
from .entities import JOKE_GENERATION_KIND, JokeGenerationInput, JokeGenerationJob


class JokeGenerationService:
    """Orchestrates creation, listing, retrieval, and deletion of joke jobs."""

    def __init__(self, async_job_repo: AsyncJobRepository, job_queue: JobQueue):
        """Initializes the service with its dependencies.

        Args:
            async_job_repo: Repository for unified async job records.
            job_queue: Queue used to dispatch background jobs.
        """
        self._async_job_repo = async_job_repo
        self._job_queue = job_queue

    def create_request(self, subject: User, course_id: int, prompt: str) -> AsyncJob:
        """Creates a joke generation job and enqueues it for processing.

        Args:
            subject: The authenticated instructor submitting the request.
            course_id: Primary key of the course.
            prompt: Description of the topic to generate jokes about.

        Returns:
            The persisted async job in PENDING status.
        """
        input_data = JokeGenerationInput(prompt=prompt).model_dump()
        job = self._async_job_repo.create(
            AsyncJob(
                course_id=course_id,
                created_by_pid=subject.pid,
                kind=JOKE_GENERATION_KIND,
                status=AsyncJobStatus.PENDING,
                input_data=input_data,
            )
        )
        assert job.id is not None
        self._job_queue.enqueue(JokeGenerationJob(job_id=job.id))
        return job

    def list_requests(self, course_id: int) -> list[AsyncJob]:
        """Returns all joke generation jobs for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of async jobs ordered by creation time descending.
        """
        return self._async_job_repo.list_by_course_and_kind(course_id, JOKE_GENERATION_KIND)

    def get_request(self, job_id: int) -> AsyncJob | None:
        """Returns a single joke generation job by ID.

        Args:
            job_id: Primary key of the async job.

        Returns:
            The matching job, or ``None`` if not found.
        """
        return self._async_job_repo.get_by_id(job_id)

    def delete_request(self, job_id: int) -> None:
        """Deletes a joke generation job.

        Args:
            job_id: Primary key of the async job to delete.

        Raises:
            ValueError: If the job does not exist.
        """
        job = self._async_job_repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        self._async_job_repo.delete(job)
