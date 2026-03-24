"""Background job for processing roster CSV uploads."""

from typing import Literal

from ..interfaces import Job, JobHandler


class _NoopJobQueue:
    """Null job queue used when submitting new jobs is not needed."""

    def enqueue(self, job: Job) -> None:
        pass


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
        on failure, and always closes the session.

        Args:
            job: Job payload containing the upload job ID.
        """
        from sqlmodel import Session as _Session

        from ..db import get_engine
        from ..repositories.membership_repository import MembershipRepository
        from ..repositories.roster_upload_repository import RosterUploadRepository
        from ..repositories.user_repository import UserRepository
        from ..services.roster_upload_service import RosterUploadService

        engine = get_engine()
        with _Session(engine) as session:
            upload_repo = RosterUploadRepository(session)
            user_repo = UserRepository(session)
            membership_repo = MembershipRepository(session)
            svc = RosterUploadService(
                upload_repo, user_repo, membership_repo, _NoopJobQueue()
            )
            try:
                svc.process_upload(job.job_id)
                session.commit()
            except Exception:
                session.rollback()
                svc.mark_failed(job.job_id)
                session.commit()
                raise
