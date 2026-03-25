"""Background job for processing roster CSV uploads."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..interfaces import TrackedJob
from .base_job_handler import BaseJobHandler

if TYPE_CHECKING:
    from sqlmodel import Session


class RosterUploadJob(TrackedJob):
    """Payload for a roster CSV upload background job."""

    type: Literal["roster_upload"] = "roster_upload"
    job_id: int


class RosterUploadJobHandler(BaseJobHandler[RosterUploadJob]):
    """Processes a queued roster upload.

    Session lifecycle, commit/rollback, and notification are handled by
    :class:`BaseJobHandler`.  This handler only implements the domain
    logic: constructing the service and calling ``process_upload``.
    """

    def _execute(self, session: "Session", job: RosterUploadJob) -> None:
        """Constructs repositories and processes the roster CSV.

        Args:
            session: Database session managed by the base handler.
            job: Job payload containing the upload job ID.
        """
        from ..repositories.async_job_repository import AsyncJobRepository
        from ..repositories.membership_repository import MembershipRepository
        from ..repositories.user_repository import UserRepository
        from ..services.roster_upload_service import RosterUploadService

        from .forbidden_job_queue import ForbiddenJobQueue

        async_job_repo = AsyncJobRepository(session)
        user_repo = UserRepository(session)
        membership_repo = MembershipRepository(session)
        svc = RosterUploadService(
            async_job_repo, user_repo, membership_repo, ForbiddenJobQueue()
        )
        svc.process_upload(job.job_id)
