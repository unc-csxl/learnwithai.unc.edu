"""Background job handler for IYOW feedback generation."""

from datetime import datetime, timezone

from sqlmodel import Session

from ...config import get_settings
from ...jobs.base_job_handler import BaseJobHandler
from ...repositories.async_job_repository import AsyncJobRepository
from ...services.ai_completion_service import AiCompletionService
from ...tables.async_job import AsyncJobStatus
from .models import IyowFeedbackJob
from .repository import IyowActivityRepository, IyowSubmissionRepository

IYOW_SYSTEM_PROMPT = (
    "You are a helpful teaching assistant providing feedback on a "
    "student's explanation. The instructor's rubric for evaluating "
    "responses is provided below. Use it to guide your feedback but "
    "do NOT reveal the rubric contents to the student. Be encouraging "
    "and constructive. Point out what the student did well and suggest "
    "specific improvements.\n\n"
    "Rubric:\n{rubric}"
)


class IyowFeedbackJobHandler(BaseJobHandler[IyowFeedbackJob]):
    """Processes a queued IYOW feedback request via LLM.

    Session lifecycle, PROCESSING transition, commit/rollback, and
    notification are handled by :class:`BaseJobHandler`. This handler
    loads the student's response and the activity rubric, calls
    the AI completion service, and writes feedback back to the
    IYOW submission record.
    """

    def _execute(  # type: ignore[override]
        self,
        job: IyowFeedbackJob,
        session: Session,
    ) -> None:
        """Generates LLM feedback for a student IYOW submission.

        Args:
            job: Job payload containing the async job ID.
            session: Open database session shared by the handler.
        """
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError(
                "openai_api_key is not configured. "
                "Set the OPENAI_API_KEY environment variable."
            )

        async_job_repo = AsyncJobRepository(session)
        async_job = async_job_repo.get_by_id(job.job_id)
        if async_job is None:
            raise ValueError(f"AsyncJob {job.job_id} not found")

        iyow_submission_repo = IyowSubmissionRepository(session)
        iyow_submission = iyow_submission_repo.get_by_async_job_id(job.job_id)
        if iyow_submission is None:
            raise ValueError(
                f"IyowSubmission for AsyncJob {job.job_id} not found"
            )

        iyow_activity_repo = IyowActivityRepository(session)
        # Walk from iyow_submission -> base submission -> activity
        from ...repositories.submission_repository import SubmissionRepository

        submission_repo = SubmissionRepository(session)
        base_submission = submission_repo.get_by_id(iyow_submission.submission_id)
        if base_submission is None:
            raise ValueError(
                f"Submission {iyow_submission.submission_id} not found"
            )

        iyow_activity = iyow_activity_repo.get_by_activity_id(
            base_submission.activity_id
        )
        if iyow_activity is None:
            raise ValueError(
                f"IyowActivity for activity {base_submission.activity_id} not found"
            )

        system_prompt = IYOW_SYSTEM_PROMPT.format(rubric=iyow_activity.rubric)
        ai_svc = AiCompletionService(
            api_key=settings.openai_api_key, model=settings.openai_model
        )
        feedback = ai_svc.complete(
            system_prompt=system_prompt,
            user_prompt=iyow_submission.response_text,
        )

        # Store raw AI data in async_job for debugging
        async_job.input_data = {
            "system_prompt": system_prompt,
            "user_prompt": iyow_submission.response_text,
        }
        async_job.output_data = {"feedback": feedback}
        async_job.status = AsyncJobStatus.COMPLETED
        async_job.completed_at = datetime.now(timezone.utc)
        async_job_repo.update(async_job)

        # Write feedback to IYOW submission
        iyow_submission.feedback = feedback
        iyow_submission_repo.update(iyow_submission)
