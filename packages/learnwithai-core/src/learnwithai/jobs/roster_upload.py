"""Background job for processing roster CSV uploads."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..interfaces import Job, JobHandler, JobUpdate
from .forbidden_job_queue import ForbiddenJobQueue

if TYPE_CHECKING:
    from ..repositories.async_job_repository import AsyncJobRepository
    from learnwithai_jobqueue.rabbitmq_job_notifier import RabbitMQJobNotifier


class RosterUploadJob(Job):
    """Payload for a roster CSV upload background job."""

    type: Literal["roster_upload"] = "roster_upload"
    job_id: int


class RosterUploadJobHandler(JobHandler["RosterUploadJob"]):
    """Processes a queued roster upload by owning the session lifecycle."""

    def handle(self, job: RosterUploadJob) -> None:
        """Opens a session, constructs the service, and processes the upload.

        Mirrors how FastAPI's ``get_session`` dependency manages the session
        lifecycle for HTTP request handlers: commits on success, rolls back
        on failure, and always closes the session. Publishes a job update
        notification after completion (success or failure).

        Args:
            job: Job payload containing the upload job ID.
        """
        from sqlmodel import Session as _Session

        from ..config import get_settings
        from ..db import get_engine
        from ..repositories.async_job_repository import AsyncJobRepository
        from ..repositories.membership_repository import MembershipRepository
        from ..repositories.user_repository import UserRepository
        from ..services.roster_upload_service import RosterUploadService

        from learnwithai_jobqueue.rabbitmq_job_notifier import RabbitMQJobNotifier

        settings = get_settings()
        notifier = RabbitMQJobNotifier(settings.effective_rabbitmq_url)

        engine = get_engine()
        with _Session(engine) as session:
            async_job_repo = AsyncJobRepository(session)
            user_repo = UserRepository(session)
            membership_repo = MembershipRepository(session)
            svc = RosterUploadService(
                async_job_repo, user_repo, membership_repo, ForbiddenJobQueue()
            )
            try:
                svc.process_upload(job.job_id)
                session.commit()
                self._notify(notifier, job.job_id, async_job_repo)
            except Exception:
                session.rollback()
                svc.mark_failed(job.job_id)
                session.commit()
                self._notify(notifier, job.job_id, async_job_repo)
                raise

    def _notify(
        self,
        notifier: "RabbitMQJobNotifier",
        job_id: int,
        async_job_repo: "AsyncJobRepository",
    ) -> None:
        """Publishes a job update notification after commit.

        Best-effort: swallows all exceptions so notification failures
        never crash the handler.

        Args:
            notifier: The notifier to publish through.
            job_id: The job ID to look up.
            async_job_repo: Repository to reload the job for current state.
        """
        try:
            reloaded = async_job_repo.get_by_id(job_id)
            if reloaded is not None:
                notifier.notify(
                    JobUpdate(
                        job_id=job_id,
                        course_id=reloaded.course_id,
                        kind=reloaded.kind,
                        status=reloaded.status.value,
                    )
                )
        except Exception:
            pass
