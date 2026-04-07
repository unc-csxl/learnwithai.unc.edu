# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Dramatiq-backed implementation of the shared job queue interface."""

from typing import Any

import dramatiq
from learnwithai.db import add_after_commit_callback
from learnwithai.interfaces import JobHandler, JobQueue
from learnwithai.jobs import Job, get_job_handler_map, job_adapter
from sqlmodel import Session


class DramatiqJobQueue(JobQueue):
    """Submits shared job payloads to a Dramatiq actor."""

    def __init__(self, session: Session | None = None):
        """Initializes the queue.

        Args:
            session: Optional request-scoped session used to defer dispatch
                until after a successful commit.
        """
        self._session = session

    def enqueue(self, job: Job) -> None:
        """Serializes and enqueues a job for background processing.

        Args:
            job: Typed job payload to submit.
        """
        payload = job.model_dump()
        if self._session is None:
            job_queue.send(payload)
            return

        def _dispatch() -> None:
            job_queue.send(payload)

        add_after_commit_callback(
            self._session,
            _dispatch,
        )


@dramatiq.actor(max_retries=3)
def job_queue(payload: dict) -> None:
    """Deserializes queued payloads and dispatches them to their handler.

    Args:
        payload: Raw payload received from Dramatiq.
    """
    job: Job = job_adapter(payload)
    handler_class: type[JobHandler[Any]] = get_job_handler_map()[type(job)]
    handler: JobHandler[Any] = handler_class()
    handler.handle(job)
