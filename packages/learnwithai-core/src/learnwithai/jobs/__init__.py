import typing
from .echo import EchoJob, EchoJobHandler
from pydantic import Field, TypeAdapter
from typing import Annotated
from ..interfaces import JobHandler, Job

JobTypes = typing.Union[Job.get_job_types()]


def job_adapter(job_data: dict) -> Job:
    adapter: TypeAdapter[Job] = TypeAdapter(
        Annotated[JobTypes, Field(discriminator="type")]
    )
    return adapter.validate_python(job_data)


job_handler_map: dict[type[Job], type[JobHandler]] = {EchoJob: EchoJobHandler}


__all__ = ["Job", "EchoJob"]
