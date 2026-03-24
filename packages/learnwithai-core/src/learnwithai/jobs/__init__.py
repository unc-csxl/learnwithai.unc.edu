"""Job payload adapters and handler registration."""

from typing import Annotated, Any, TypeAlias, Union

from pydantic import Discriminator, TypeAdapter

from .echo import EchoJob, EchoJobHandler
from .roster_upload import RosterUploadJob, RosterUploadJobHandler
from ..interfaces import JobHandler, Job

JobPayload: TypeAlias = Annotated[Union[EchoJob, RosterUploadJob], Discriminator("type")]

job_payload_adapter: TypeAdapter[JobPayload] = TypeAdapter(JobPayload)


def job_adapter(job_data: dict[str, Any]) -> Job:
    """Validates raw job payloads into typed job models.

    Args:
        job_data: Untrusted job payload received from the queue.

    Returns:
        A validated job model.
    """
    return job_payload_adapter.validate_python(job_data)


job_handler_map: dict[type[Job], type[JobHandler[Any]]] = {
    EchoJob: EchoJobHandler,
    RosterUploadJob: RosterUploadJobHandler,
}


__all__ = ["Job", "EchoJob", "RosterUploadJob", "JobPayload"]
