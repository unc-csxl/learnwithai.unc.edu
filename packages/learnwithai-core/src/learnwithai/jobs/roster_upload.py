"""Background job for processing roster CSV uploads."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

from fast_depends import Depends

from ..di import roster_upload_service_handler_factory
from ..interfaces import TrackedJob
from .base_job_handler import BaseJobHandler

if TYPE_CHECKING:
    from ..services.roster_upload_service import RosterUploadService


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
    :class:`BaseJobHandler`.  Dependencies are resolved via
    ``fast-depends`` — see :mod:`learnwithai.di`.
    """

    def _execute(  # type: ignore[override]
        self,
        job: RosterUploadJob,
        svc: RosterUploadService = Depends(roster_upload_service_handler_factory),
    ) -> None:
        """Delegates to the roster upload service.

        Args:
            job: Job payload containing the upload job ID.
            svc: Injected roster upload service.
        """
        svc.process_upload(job.job_id)
