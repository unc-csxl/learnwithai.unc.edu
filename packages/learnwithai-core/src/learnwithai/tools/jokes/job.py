"""Background job handler for joke generation."""

from datetime import datetime, timezone

from sqlmodel import Session

from ...config import get_settings
from ...jobs.base_job_handler import BaseJobHandler
from ...repositories.async_job_repository import AsyncJobRepository
from ...services.ai_completion_service import AiCompletionService
from ...tables.async_job import AsyncJobStatus
from .models import JokeGenerationJob
from .repository import JokeRepository

JOKE_SYSTEM_PROMPT = (
    "You are a witty comedy writer who specializes in educational humor. "
    "The user will describe a course topic and you will generate jokes "
    "related to that topic that an instructor could use to add humor to "
    "their lectures. Return exactly {count} jokes, one per line. Do not "
    "number them. Each joke should be self-contained and concise."
)

DEFAULT_JOKE_COUNT = 5


class JokeGenerationJobHandler(BaseJobHandler[JokeGenerationJob]):
    """Processes a queued joke generation request.

    Session lifecycle, PROCESSING transition, commit/rollback, and
    notification are handled by :class:`BaseJobHandler`. This handler
    loads the Joke, calls the AI completion service, parses
    jokes, and writes results to both the Joke and AsyncJob.
    """

    def _execute(  # type: ignore[override]
        self,
        job: JokeGenerationJob,
        session: Session,
    ) -> None:
        """Generates jokes via AiCompletionService and persists the results.

        Args:
            job: Job payload containing the async job ID.
            session: Open database session shared by the handler.
        """
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("openai_api_key is not configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY.")

        async_job_repo = AsyncJobRepository(session)
        async_job = async_job_repo.get_by_id(job.job_id)
        if async_job is None:
            raise ValueError(f"AsyncJob {job.job_id} not found")

        joke_repo = JokeRepository(session)
        joke = joke_repo.get_by_async_job_id(job.job_id)
        if joke is None:
            raise ValueError(f"Joke for AsyncJob {job.job_id} not found")

        system_prompt = JOKE_SYSTEM_PROMPT.format(count=DEFAULT_JOKE_COUNT)
        ai_svc = AiCompletionService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            endpoint=settings.openai_endpoint,
            api_version=settings.openai_api_version,
        )
        raw_response = ai_svc.complete(system_prompt=system_prompt, user_prompt=joke.prompt)

        jokes = _parse_jokes(raw_response, DEFAULT_JOKE_COUNT)

        # Store raw AI data in async_job for debugging
        async_job.input_data = {"system_prompt": system_prompt, "user_prompt": joke.prompt}
        async_job.output_data = {"raw_response": raw_response}
        async_job.status = AsyncJobStatus.COMPLETED
        async_job.completed_at = datetime.now(timezone.utc)
        async_job_repo.update(async_job)

        # Store parsed feature data in joke
        joke.jokes = jokes
        joke_repo.update(joke)


def _parse_jokes(content: str, count: int) -> list[str]:
    """Splits the AI response content into individual jokes.

    Filters blank lines and strips leading numbering (e.g. ``1.``)
    in case the model numbers them despite instructions.

    Args:
        content: Raw response text from the model.
        count: Maximum number of jokes to return.

    Returns:
        A list of cleaned joke strings, at most *count* items.
    """
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    jokes: list[str] = []
    for line in lines:
        cleaned = line.lstrip("0123456789").lstrip(".)")
        cleaned = cleaned.strip()
        if cleaned:
            jokes.append(cleaned)
        if len(jokes) >= count:
            break
    return jokes
