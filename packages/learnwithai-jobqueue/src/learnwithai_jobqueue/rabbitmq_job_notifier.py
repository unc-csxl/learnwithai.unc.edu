# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""RabbitMQ-backed job notifier that publishes updates to a fanout exchange."""

import json
import logging

import pika
from learnwithai.interfaces.jobs import JobNotifier, JobUpdate
from pika.adapters.blocking_connection import BlockingChannel

logger = logging.getLogger(__name__)

JOB_UPDATES_EXCHANGE = "job_updates"


class RabbitMQJobNotifier(JobNotifier):
    """Publishes job status updates to the ``job_updates`` fanout exchange.

    Uses a synchronous ``pika`` connection suitable for Dramatiq worker
    processes. The connection is established lazily on the first call to
    :meth:`notify` and reused for subsequent calls. If the connection
    drops, the next call will re-establish it.
    """

    def __init__(self, rabbitmq_url: str):
        """Initializes the notifier with a RabbitMQ connection URL.

        Args:
            rabbitmq_url: AMQP URL used to connect to RabbitMQ.
        """
        self._rabbitmq_url = rabbitmq_url
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def notify(self, update: JobUpdate) -> None:
        """Publishes a job update to the fanout exchange.

        Establishes or re-establishes the RabbitMQ connection if needed.
        Logs and swallows errors so that notification failures never crash
        the job handler.

        Args:
            update: The job status change to broadcast.
        """
        try:
            channel = self._ensure_channel()
            body = json.dumps(update.model_dump()).encode("utf-8")
            channel.basic_publish(
                exchange=JOB_UPDATES_EXCHANGE,
                routing_key="",
                body=body,
                properties=pika.BasicProperties(content_type="application/json"),
            )
        except Exception:
            logger.exception("Failed to publish job update for job %d", update.job_id)
            self.close()

    def _ensure_channel(
        self,
    ) -> BlockingChannel:
        """Returns a usable channel, creating a new connection if necessary.

        Returns:
            An open pika channel with the fanout exchange declared.
        """
        if self._connection is None or self._connection.is_closed:
            self._connection = pika.BlockingConnection(pika.URLParameters(self._rabbitmq_url))
            self._channel = None

        if self._channel is None or self._channel.is_closed:
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange=JOB_UPDATES_EXCHANGE,
                exchange_type="fanout",
                durable=True,
            )

        return self._channel

    def close(self) -> None:
        """Closes the connection and resets internal state.

        Called by :meth:`BaseJobHandler.handle` after each job so that
        connections do not accumulate across messages.
        """
        try:
            if self._connection is not None and self._connection.is_open:
                self._connection.close()
        except Exception:
            pass
        finally:
            self._connection = None
            self._channel = None
