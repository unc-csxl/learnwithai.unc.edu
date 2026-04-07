# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""RabbitMQ consumer that bridges job update messages to WebSocket clients.

Connects to the ``job_updates`` fanout exchange via ``aio-pika`` and
forwards each message to the :class:`~api.realtime.manager.JobUpdateManager`
for delivery over open WebSocket connections.
"""

from __future__ import annotations

import asyncio
import logging

from learnwithai.config import Settings
from learnwithai.interfaces.jobs import JobUpdate

from api.realtime.manager import JobUpdateManager

logger = logging.getLogger(__name__)


async def handle_job_update_message(manager: JobUpdateManager, body: bytes) -> None:
    """Parses a raw message body and broadcasts the job update.

    Args:
        manager: The in-memory subscription manager to broadcast through.
        body: Raw JSON bytes from the RabbitMQ message.
    """
    update = JobUpdate.model_validate_json(body)
    await manager.broadcast(update)


async def consume_job_updates(  # pragma: no cover — requires live RabbitMQ
    manager: JobUpdateManager, settings: Settings
) -> None:
    """Background task that consumes job updates from RabbitMQ and broadcasts.

    Connects to the ``job_updates`` fanout exchange via ``aio-pika``,
    creates an exclusive auto-delete queue, and forwards every message
    to the :class:`JobUpdateManager`.  Reconnects automatically on
    connection loss.

    Args:
        manager: The in-memory subscription manager to broadcast through.
        settings: Application settings containing the RabbitMQ URL.
    """
    import aio_pika

    exchange_name = "job_updates"

    while True:
        connection = None
        try:
            connection = await aio_pika.connect(settings.effective_rabbitmq_url)
            channel = await connection.channel()
            exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT, durable=True)
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(exchange)

            logger.info("WebSocket consumer connected to RabbitMQ.")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            await handle_job_update_message(manager, message.body)
                        except Exception:
                            logger.exception("Failed to process job update message.")
        except asyncio.CancelledError:
            logger.info("WebSocket consumer task cancelled.")
            if connection and not connection.is_closed:
                await connection.close()
            return
        except Exception:
            logger.exception("RabbitMQ consumer connection lost. Reconnecting in 5s.")
            if connection and not connection.is_closed:
                try:
                    await connection.close()
                except Exception:
                    pass
            await asyncio.sleep(5)
