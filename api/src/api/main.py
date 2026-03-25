"""Application entrypoint for the FastAPI adapter."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from api.job_update_manager import JobUpdateManager
from api.openapi import API_DESCRIPTION, OPENAPI_TAGS
from api.routes import API_ROUTERS
from api.routes.dev import router as dev_router
from api.routes import ws as ws_route_module
from api.spa import configure_spa

from learnwithai.config import Settings
from learnwithai.errors import AuthorizationError
from learnwithai.interfaces.jobs import JobUpdate

logger = logging.getLogger(__name__)


def _generate_operation_id(route: APIRoute) -> str:
    """Uses the Python function name as the OpenAPI operationId.

    FastAPI's default includes the full URL path, which produces unwieldy
    names in generated clients (e.g. ``create_course_api_courses_post``).
    This override yields clean identifiers like ``create_course``.
    """
    return route.name


async def _handle_job_update_message(manager: JobUpdateManager, body: bytes) -> None:
    """Parses a raw message body and broadcasts the job update.

    Args:
        manager: The in-memory subscription manager to broadcast through.
        body: Raw JSON bytes from the RabbitMQ message.
    """
    update = JobUpdate.model_validate_json(body)
    await manager.broadcast(update)


async def _consume_job_updates(  # pragma: no cover — requires live RabbitMQ
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
            exchange = await channel.declare_exchange(
                exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
            )
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(exchange)

            logger.info("WebSocket consumer connected to RabbitMQ.")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            await _handle_job_update_message(manager, message.body)
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


@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Manages startup and shutdown of background resources.

    Starts the RabbitMQ consumer background task on startup and
    cancels it on shutdown.  Skips the consumer in test environments
    where RabbitMQ is not available.
    """
    manager = JobUpdateManager()
    ws_route_module.configure(manager)
    application.include_router(ws_route_module.router, prefix="/api")

    current_settings = Settings()
    consumer_task: asyncio.Task[None] | None = None

    if not current_settings.is_test:  # pragma: no cover — no RabbitMQ in tests
        consumer_task = asyncio.create_task(
            _consume_job_updates(manager, current_settings)
        )

    yield

    if consumer_task is not None:  # pragma: no cover — only when consumer started
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


def create_app(settings: Settings) -> FastAPI:
    """Creates and configures the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        generate_unique_id_function=_generate_operation_id,
        lifespan=_lifespan,
    )

    @application.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        _request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    for router in API_ROUTERS:
        application.include_router(router, prefix="/api")

    if settings.is_development:
        application.include_router(dev_router, prefix="/api")

    configure_spa(application, settings)
    return application


settings = Settings()
app = create_app(settings)
