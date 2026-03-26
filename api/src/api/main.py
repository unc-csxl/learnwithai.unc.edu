"""Application entrypoint for the FastAPI adapter.

Creates and configures the FastAPI application by composing routes,
middleware, and lifecycle hooks.  Implementation details live in
dedicated modules; this file reads as a high-level wiring overview.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from learnwithai.config import Settings
from learnwithai.errors import AuthorizationError

from api.lifespan import lifespan
from api.openapi import API_DESCRIPTION, OPENAPI_TAGS, generate_operation_id
from api.routes import API_ROUTERS
from api.routes import ws as ws_route_module
from api.routes.dev import router as dev_router
from api.spa import configure_spa


def create_app(settings: Settings) -> FastAPI:
    """Creates and configures the FastAPI application."""
    # Core application with OpenAPI metadata and lifecycle hooks
    application = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        generate_unique_id_function=generate_operation_id,
        lifespan=lifespan,
    )

    # Map domain authorization errors to 403 responses
    @application.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        _request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    # Mount REST API routes under /api
    for router in API_ROUTERS:
        application.include_router(router, prefix="/api")

    # Mount WebSocket endpoint for real-time job updates
    application.include_router(ws_route_module.router, prefix="/api")

    # Development-only routes (dev data seeding, utilities)
    if settings.is_development:
        application.include_router(dev_router, prefix="/api")

    # Serve the Angular SPA for all non-API routes
    configure_spa(application, settings)
    return application


settings = Settings()
app = create_app(settings)
