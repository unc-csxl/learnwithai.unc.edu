# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Application lifespan manager for background resource lifecycle.

Phases:
    **Startup** — Creates the :class:`~api.realtime.manager.JobUpdateManager`,
    wires it into the WebSocket route module, and launches the RabbitMQ
    consumer background task (skipped in test environments).

    **Yield** — The application serves requests.

    **Shutdown** — Cancels the consumer task and waits for it to finish.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from learnwithai.config import Settings

from api.realtime import JobUpdateManager, consume_job_updates
from api.routes import ws as ws_route_module

logger = logging.getLogger(__name__)


async def _lifespan_context(application: FastAPI) -> AsyncIterator[None]:
    """Manages startup and shutdown of background resources.

    Starts the RabbitMQ consumer background task on startup and
    cancels it on shutdown.  Skips the consumer in test environments
    where RabbitMQ is not available.
    """
    manager = JobUpdateManager()
    ws_route_module.configure(manager)

    current_settings = Settings()
    consumer_task: asyncio.Task[None] | None = None

    if not current_settings.is_test:
        consumer_task = asyncio.create_task(consume_job_updates(manager, current_settings))

    yield

    if consumer_task is not None:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


lifespan = asynccontextmanager(_lifespan_context)
