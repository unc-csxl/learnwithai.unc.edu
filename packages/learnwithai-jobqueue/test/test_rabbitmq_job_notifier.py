"""Tests for the RabbitMQ job notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from learnwithai.interfaces.jobs import JobNotifier, JobUpdate
from learnwithai_jobqueue.rabbitmq_job_notifier import (
    JOB_UPDATES_EXCHANGE,
    RabbitMQJobNotifier,
)


def _make_update() -> JobUpdate:
    return JobUpdate(
        job_id=42, course_id=7, kind="roster_upload", status="completed"
    )


def test_rabbitmq_job_notifier_satisfies_protocol() -> None:
    notifier = RabbitMQJobNotifier("amqp://guest:guest@localhost/")
    assert isinstance(notifier, JobNotifier)


def test_notify_publishes_json_to_fanout_exchange() -> None:
    # Arrange
    notifier = RabbitMQJobNotifier("amqp://guest:guest@localhost/")
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.is_closed = False
    mock_channel.is_closed = False
    mock_connection.channel.return_value = mock_channel
    update = _make_update()

    # Act
    with patch(
        "learnwithai_jobqueue.rabbitmq_job_notifier.pika.BlockingConnection",
        return_value=mock_connection,
    ):
        notifier.notify(update)

    # Assert
    mock_channel.exchange_declare.assert_called_once_with(
        exchange=JOB_UPDATES_EXCHANGE,
        exchange_type="fanout",
        durable=True,
    )
    mock_channel.basic_publish.assert_called_once()
    call_kwargs = mock_channel.basic_publish.call_args
    assert call_kwargs.kwargs["exchange"] == JOB_UPDATES_EXCHANGE
    assert call_kwargs.kwargs["routing_key"] == ""
    assert b'"job_id": 42' in call_kwargs.kwargs["body"]


def test_notify_reuses_existing_connection() -> None:
    # Arrange
    notifier = RabbitMQJobNotifier("amqp://guest:guest@localhost/")
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.is_closed = False
    mock_channel.is_closed = False
    mock_connection.channel.return_value = mock_channel
    update = _make_update()

    with patch(
        "learnwithai_jobqueue.rabbitmq_job_notifier.pika.BlockingConnection",
        return_value=mock_connection,
    ) as conn_cls:
        notifier.notify(update)
        notifier.notify(update)

    # Assert — connection created once, published twice
    conn_cls.assert_called_once()
    assert mock_channel.basic_publish.call_count == 2


def test_notify_recovers_from_closed_connection() -> None:
    # Arrange
    notifier = RabbitMQJobNotifier("amqp://guest:guest@localhost/")
    mock_connection_1 = MagicMock()
    mock_channel_1 = MagicMock()
    mock_connection_1.is_closed = False
    mock_channel_1.is_closed = False
    mock_connection_1.channel.return_value = mock_channel_1

    mock_connection_2 = MagicMock()
    mock_channel_2 = MagicMock()
    mock_connection_2.is_closed = False
    mock_channel_2.is_closed = False
    mock_connection_2.channel.return_value = mock_channel_2

    update = _make_update()

    with patch(
        "learnwithai_jobqueue.rabbitmq_job_notifier.pika.BlockingConnection",
        side_effect=[mock_connection_1, mock_connection_2],
    ):
        notifier.notify(update)
        # Simulate connection drop
        mock_connection_1.is_closed = True
        notifier.notify(update)

    # Assert — second call used a new connection
    mock_channel_1.basic_publish.assert_called_once()
    mock_channel_2.basic_publish.assert_called_once()


def test_notify_swallows_publish_errors() -> None:
    # Arrange
    notifier = RabbitMQJobNotifier("amqp://guest:guest@localhost/")
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.is_closed = False
    mock_channel.is_closed = False
    mock_connection.channel.return_value = mock_channel
    mock_channel.basic_publish.side_effect = RuntimeError("connection lost")
    update = _make_update()

    # Act — should not raise
    with patch(
        "learnwithai_jobqueue.rabbitmq_job_notifier.pika.BlockingConnection",
        return_value=mock_connection,
    ):
        notifier.notify(update)

    # Assert — connection was cleaned up
    assert notifier._connection is None
    assert notifier._channel is None


def test_close_swallows_exception_during_connection_close() -> None:
    # Arrange
    notifier = RabbitMQJobNotifier("amqp://guest:guest@localhost/")
    mock_connection = MagicMock()
    mock_connection.is_open = True
    mock_connection.close.side_effect = RuntimeError("close failed")
    notifier._connection = mock_connection

    # Act — should not raise
    notifier._close()

    # Assert — state was still reset
    assert notifier._connection is None
    assert notifier._channel is None
