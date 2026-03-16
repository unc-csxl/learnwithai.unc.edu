from __future__ import annotations

from learnwithai.interfaces import Job
from learnwithai.db import Session
from unittest.mock import MagicMock

from api.context import PublicContext


class StubJobQueue:
    def enqueue(self, job: Job) -> None:
        del job


def test_context_stores_job_queue_dependency() -> None:
    # Arrange
    job_queue = StubJobQueue()
    session = MagicMock(spec=Session)

    # Act
    context = PublicContext(job_queue=job_queue, session=session)

    # Assert
    assert context.job_queue is job_queue
