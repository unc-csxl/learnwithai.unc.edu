from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from learnwithai.jobs import EchoJob
from learnwithai_jobqueue.dramatiq_job_queue import DramatiqJobQueue, job_queue


def test_enqueue_sends_serialized_job_payload() -> None:
    # Arrange
    queue = DramatiqJobQueue()
    job = EchoJob(message="hello")

    # Act
    with patch("learnwithai_jobqueue.dramatiq_job_queue.job_queue.send") as send_mock:
        queue.enqueue(job)

    # Assert
    send_mock.assert_called_once_with({"type": "echo", "message": "hello"})


def test_enqueue_defers_dispatch_until_after_commit_when_session_bound() -> None:
    # Arrange
    session = Mock()
    queue = DramatiqJobQueue(session=session)
    job = EchoJob(message="hello")

    # Act
    with (
        patch("learnwithai_jobqueue.dramatiq_job_queue.add_after_commit_callback") as callback_mock,
        patch("learnwithai_jobqueue.dramatiq_job_queue.job_queue.send") as send_mock,
    ):
        queue.enqueue(job)

        # Assert
        callback_mock.assert_called_once()
        assert callback_mock.call_args.args[0] is session
        send_mock.assert_not_called()

        deferred_send = callback_mock.call_args.args[1]
        deferred_send()
        send_mock.assert_called_once_with({"type": "echo", "message": "hello"})


def test_job_queue_actor_dispatches_to_handler_class() -> None:
    # Arrange
    job = EchoJob(message="hello")
    handler = Mock()
    handler_class = Mock(return_value=handler)
    payload = {"type": "echo", "message": "hello"}

    # Act
    with (
        patch("learnwithai_jobqueue.dramatiq_job_queue.job_adapter", return_value=job),
        patch(
            "learnwithai_jobqueue.dramatiq_job_queue.get_job_handler_map",
            return_value={EchoJob: handler_class},
        ),
    ):
        job_queue.fn(payload)

    # Assert
    handler_class.assert_called_once_with()
    handler.handle.assert_called_once_with(job)


@pytest.mark.integration
def test_job_queue_actor_integrates_adapter_and_handler() -> None:
    # Arrange
    payload = {"type": "echo", "message": "hello"}
    expected_status = {"status": "ok", "environment": "test"}

    # Act
    with (
        patch("learnwithai.jobs.echo.get_health_status", return_value=expected_status),
        patch("builtins.print") as print_mock,
    ):
        job_queue.fn(payload)

    # Assert
    print_mock.assert_called_once()
    printed_payload = print_mock.call_args.args[0]
    assert printed_payload["task"] == "echo_job"
    assert printed_payload["payload"].message == "hello"
    assert printed_payload["core_status"] == expected_status


def test_job_queue_actor_limits_retries() -> None:
    """max_retries prevents retry storms from configuration errors."""
    assert job_queue.options.get("max_retries") == 3
