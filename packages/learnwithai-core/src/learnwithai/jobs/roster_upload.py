"""Background job for processing roster CSV uploads."""

from typing import Literal

from ..interfaces import Job, JobHandler
from ..services.roster_upload_service import process_roster_upload


class RosterUploadJob(Job):
    """Payload for a roster CSV upload background job."""

    type: Literal["roster_upload"] = "roster_upload"
    job_id: int


class RosterUploadJobHandler(JobHandler["RosterUploadJob"]):
    """Processes a queued roster upload by delegating to the service layer."""

    def handle(self, job: RosterUploadJob) -> None:
        """Handles a roster upload job.

        Args:
            job: Job payload containing the upload job ID.
        """
        process_roster_upload(job.job_id)
