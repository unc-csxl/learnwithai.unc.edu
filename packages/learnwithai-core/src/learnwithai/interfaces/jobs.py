"""Contracts for serializable background jobs and their handlers."""

from abc import ABC
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel


class Job(BaseModel, ABC):
    """Base model for background jobs passed between services."""

    pass


@runtime_checkable
class SupportsJobType(Protocol):
    """Protocol for payloads that expose a stable job type string."""

    @property
    def type(self) -> str: ...


JobT = TypeVar("JobT", bound=Job, contravariant=True)


class JobQueue(Protocol):
    """Queue interface for submitting jobs for asynchronous execution."""

    def enqueue(self, job: Job) -> None: ...


class JobHandler(Protocol[JobT]):
    """Handler interface for executing a specific job type."""

    def handle(self, job: JobT) -> None: ...
