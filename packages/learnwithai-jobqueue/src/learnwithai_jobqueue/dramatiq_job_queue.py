"""Dramatiq-backed implementation of the shared job queue interface."""

from typing import Any

import dramatiq

from learnwithai.interfaces import JobQueue, JobHandler
from learnwithai.jobs import Job, job_handler_map, job_adapter


class DramatiqJobQueue(JobQueue):
    """Submits shared job payloads to a Dramatiq actor."""

    def enqueue(self, job: Job) -> None:
        """Serializes and enqueues a job for background processing.

        Args:
            job: Typed job payload to submit.
        """
        job_queue.send(job.model_dump())


@dramatiq.actor
def job_queue(payload: dict) -> None:
    """Deserializes queued payloads and dispatches them to their handler.

    Args:
        payload: Raw payload received from Dramatiq.
    """
    job: Job = job_adapter(payload)
    handler_class: type[JobHandler[Any]] = job_handler_map[type(job)]
    handler: JobHandler[Any] = handler_class()
    handler.handle(job)
