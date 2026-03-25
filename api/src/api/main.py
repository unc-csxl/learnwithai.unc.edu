"""Application entrypoint for the FastAPI adapter.

Creates and configures the FastAPI application, wires up routes, and
manages the application lifespan (background consumer startup/shutdown).
Implementation details for the RabbitMQ consumer live in
:mod:`api.job_update_consumer`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from api.job_update_consumer import consume_job_updates
from api.job_update_manager import JobUpdateManager
from api.openapi import API_DESCRIPTION, OPENAPI_TAGS
from api.routes import API_ROUTERS
from api.routes.dev import router as dev_router
from api.routes import ws as ws_route_module
from api.spa import configure_spa

from learnwithai.config import Settings
from learnwithai.errors import AuthorizationError

logger = logging.getLogger(__name__)


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
            consume_job_updates(manager, current_settings)
        )

    yield

    if consumer_task is not None:  # pragma: no cover — only when consumer started
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


def _generate_operation_id(route: APIRoute) -> str:
    """Uses the Python function name as the OpenAPI operationId.

    FastAPI's default includes the full URL path, which produces unwieldy
    names in generated clients (e.g. ``create_course_api_courses_post``).
    This override yields clean identifiers like ``create_course``.
    """
    return route.name


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
