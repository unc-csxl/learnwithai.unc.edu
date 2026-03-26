"""Contracts for serializable background jobs and their handlers."""

from abc import ABC
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel


class Job(BaseModel, ABC):
    """Base model for background jobs passed between services."""

    pass


class TrackedJob(Job):
    """A Job whose execution is tracked by a persistent ``AsyncJob`` row.

    All jobs processed through :class:`BaseJobHandler` must extend this
    so the handler can locate the corresponding database record.
    """

    job_id: int


@runtime_checkable
class SupportsJobType(Protocol):
    """Protocol for payloads that expose a stable job type string."""

    @property
    def type(self) -> str: ...


JobT = TypeVar("JobT", bound=Job, contravariant=True)


@runtime_checkable
class JobQueue(Protocol):
    """Queue interface for submitting jobs for asynchronous execution."""

    def enqueue(self, job: Job) -> None: ...


class JobHandler(Protocol[JobT]):
    """Handler interface for executing a specific job type."""

    def handle(self, job: JobT) -> None: ...


class JobUpdate(BaseModel):
    """Lightweight notification published when a job's status changes."""

    job_id: int
    course_id: int
    user_id: int
    kind: str
    status: str


@runtime_checkable
class JobNotifier(Protocol):
    """Publishes job status changes to interested listeners."""

    def notify(self, update: JobUpdate) -> None: ...


@runtime_checkable
class NotifierCloseable(Protocol):
    """Notifier that holds resources which should be explicitly released."""

    def close(self) -> None: ...
