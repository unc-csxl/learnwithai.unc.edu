from typing import Protocol
from pydantic import BaseModel
from abc import ABC


class Job(BaseModel, ABC):
    type: str

    @classmethod
    def get_job_types(cls):
        return tuple(cls.__subclasses__())


class JobQueue(Protocol):
    def enqueue(self, job: Job) -> None: ...


class JobHandler(Protocol):
    def handle(self, job: Job) -> None: ...
