from typing import Any, TypeAlias

from pydantic import TypeAdapter

from .echo import EchoJob, EchoJobHandler
from ..interfaces import JobHandler, Job

JobPayload: TypeAlias = EchoJob

job_payload_adapter: TypeAdapter[JobPayload] = TypeAdapter(JobPayload)


def job_adapter(job_data: dict[str, Any]) -> Job:
    return job_payload_adapter.validate_python(job_data)


job_handler_map: dict[type[Job], type[JobHandler[Any]]] = {EchoJob: EchoJobHandler}


__all__ = ["Job", "EchoJob", "JobPayload"]
