"""Job payload adapters and handler registration."""

from typing import Annotated, Any, TypeAlias, Union

from pydantic import Discriminator, TypeAdapter

from ..interfaces import Job, JobHandler
from ..tools.jokes.entities import JokeGenerationJob
from .base_job_handler import BaseJobHandler
from .echo import EchoJob, EchoJobHandler
from .forbidden_job_queue import ForbiddenJobQueue
from .noop_job_notifier import NoOpJobNotifier
from .roster_upload import RosterUploadJob, RosterUploadJobHandler, RosterUploadOutput

JobPayload: TypeAlias = Annotated[
    Union[EchoJob, JokeGenerationJob, RosterUploadJob], Discriminator("type")
]

job_payload_adapter: TypeAdapter[JobPayload] = TypeAdapter(JobPayload)


def job_adapter(job_data: dict[str, Any]) -> Job:
    """Validates raw job payloads into typed job models.

    Args:
        job_data: Untrusted job payload received from the queue.

    Returns:
        A validated job model.
    """
    return job_payload_adapter.validate_python(job_data)


def get_job_handler_map() -> dict[type[Job], type[JobHandler[Any]]]:
    """Returns the handler map with a lazy import to avoid circular imports.

    The ``JokeGenerationJobHandler`` lives in ``tools.jokes.job`` which
    imports ``BaseJobHandler`` from this package.  A module-level
    import would create a cycle, so the handler is resolved lazily.
    """
    from ..tools.jokes.job import JokeGenerationJobHandler

    return {
        EchoJob: EchoJobHandler,
        JokeGenerationJob: JokeGenerationJobHandler,
        RosterUploadJob: RosterUploadJobHandler,
    }


__all__ = [
    "BaseJobHandler",
    "Job",
    "EchoJob",
    "ForbiddenJobQueue",
    "JokeGenerationJob",
    "NoOpJobNotifier",
    "RosterUploadJob",
    "RosterUploadOutput",
    "JobPayload",
    "get_job_handler_map",
]
