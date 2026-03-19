"""Application entrypoint for the FastAPI adapter."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from api.openapi import API_DESCRIPTION, OPENAPI_TAGS
from api.routes import API_ROUTERS
from api.routes.dev import router as dev_router
from api.spa import configure_spa

from learnwithai.config import Settings
from learnwithai.errors import AuthorizationError


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
