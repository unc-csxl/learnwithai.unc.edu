from abc import ABC
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel


class Job(BaseModel, ABC):
    pass


@runtime_checkable
class SupportsJobType(Protocol):
    @property
    def type(self) -> str: ...


JobT = TypeVar("JobT", bound=Job, contravariant=True)


class JobQueue(Protocol):
    def enqueue(self, job: Job) -> None: ...


class JobHandler(Protocol[JobT]):
    def handle(self, job: JobT) -> None: ...
