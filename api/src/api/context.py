from typing import Annotated, TypeAlias
from fastapi import Depends
from .job_queue import JobQueueDI


class Context:
    def __init__(self, job_queue: JobQueueDI):
        self.job_queue = job_queue


ContextDI: TypeAlias = Annotated[Context, Depends()]
