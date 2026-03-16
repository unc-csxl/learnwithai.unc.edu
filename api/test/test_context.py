from __future__ import annotations

from api.context import Context


def test_context_stores_job_queue_dependency() -> None:
    # Arrange
    job_queue = object()

    # Act
    context = Context(job_queue=job_queue)

    # Assert
    assert context.job_queue is job_queue