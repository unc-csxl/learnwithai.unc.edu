from __future__ import annotations

from unittest.mock import patch

from api.job_queue import job_queue_factory


def test_job_queue_factory_builds_dramatiq_job_queue() -> None:
    # Arrange
    expected_queue = object()

    # Act
    with patch("api.job_queue.DramatiqJobQueue", return_value=expected_queue) as queue_class_mock:
        job_queue = job_queue_factory()

    # Assert
    assert job_queue is expected_queue
    queue_class_mock.assert_called_once_with()