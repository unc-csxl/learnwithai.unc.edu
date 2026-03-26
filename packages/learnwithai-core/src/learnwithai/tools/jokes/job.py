"""Background job handler for joke generation."""

from datetime import datetime, timezone

from sqlmodel import Session

from ...config import get_settings
from ...jobs.base_job_handler import BaseJobHandler
from ...repositories.async_job_repository import AsyncJobRepository
from ...tables.async_job import AsyncJobStatus
from .models import JokeGenerationJob, JokeGenerationOutput
from .openai_service import OpenAIService


class JokeGenerationJobHandler(BaseJobHandler[JokeGenerationJob]):
    """Processes a queued joke generation request.

    Session lifecycle, PROCESSING transition, commit/rollback, and
    notification are handled by :class:`BaseJobHandler`. This handler
    extracts the prompt, calls OpenAI, and stores the generated jokes.
    """

    def _execute(  # type: ignore[override]
        self,
        job: JokeGenerationJob,
        session: Session,
    ) -> None:
        """Generates jokes via OpenAI and persists the results.

        Args:
            job: Job payload containing the async job ID.
            session: Open database session shared by the handler.
        """
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("openai_api_key is not configured. Set the OPENAI_API_KEY environment variable.")

        repo = AsyncJobRepository(session)
        async_job = repo.get_by_id(job.job_id)
        if async_job is None:
            raise ValueError(f"AsyncJob {job.job_id} not found")

        prompt = async_job.input_data.get("prompt", "")
        openai_svc = OpenAIService(api_key=settings.openai_api_key, model=settings.openai_model)
        jokes = openai_svc.generate_jokes(prompt)

        async_job.output_data = JokeGenerationOutput(jokes=jokes).model_dump()
        async_job.status = AsyncJobStatus.COMPLETED
        async_job.completed_at = datetime.now(timezone.utc)
        repo.update(async_job)
