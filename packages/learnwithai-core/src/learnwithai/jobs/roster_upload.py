"""Background job for processing roster CSV uploads."""

from typing import Literal, TypedDict

from sqlmodel import Session

from ..interfaces import TrackedJob
from ..repositories.async_job_repository import AsyncJobRepository
from ..repositories.membership_repository import MembershipRepository
from ..repositories.user_repository import UserRepository
from .base_job_handler import BaseJobHandler
from .forbidden_job_queue import ForbiddenJobQueue


class RosterUploadOutput(TypedDict):
    """Shape of ``AsyncJob.output_data`` written by roster upload jobs."""

    created_count: int
    updated_count: int
    error_count: int
    error_details: str | None


class RosterUploadJob(TrackedJob):
    """Payload for a roster CSV upload background job."""

    type: Literal["roster_upload"] = "roster_upload"
    job_id: int


class RosterUploadJobHandler(BaseJobHandler[RosterUploadJob]):
    """Processes a queued roster upload.

    Session lifecycle, commit/rollback, and notification are handled by
    :class:`BaseJobHandler`. Dependencies are constructed directly from
    the handler session.
    """

    def _execute(  # type: ignore[override]
        self,
        job: RosterUploadJob,
        session: Session,
    ) -> None:
        """Delegates to the roster upload service.

        Args:
            job: Job payload containing the upload job ID.
            session: Open database session shared by the handler.
        """
        from ..services.roster_upload_service import RosterUploadService

        svc = RosterUploadService(
            AsyncJobRepository(session),
            UserRepository(session),
            MembershipRepository(session),
            ForbiddenJobQueue(),
        )
        svc.process_upload(job.job_id)
