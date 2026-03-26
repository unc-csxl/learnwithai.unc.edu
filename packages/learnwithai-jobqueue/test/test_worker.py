from __future__ import annotations

import importlib
from unittest.mock import Mock, patch

import learnwithai_jobqueue.worker as worker


def test_worker_logs_ready_message_on_import() -> None:
    # Arrange
    logger = Mock()

    # Act
    with patch("learnwithai_jobqueue.worker.logging.getLogger", return_value=logger) as get_logger_mock:
        reloaded_worker = importlib.reload(worker)

    # Assert
    assert reloaded_worker.logger is logger
    get_logger_mock.assert_called_once_with("learnwithai_jobqueue.worker")
    logger.info.assert_called_once_with("Worker Ready")
