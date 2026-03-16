from __future__ import annotations

from learnwithai.interfaces import Job

from api.context import Context


class StubJobQueue:
    def enqueue(self, job: Job) -> None:
        del job


def test_context_stores_job_queue_dependency() -> None:
    # Arrange
    job_queue = StubJobQueue()

    # Act
    context = Context(job_queue=job_queue)

    # Assert
    assert context.job_queue is job_queue
