"""Application entrypoint for the FastAPI adapter."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.openapi import API_DESCRIPTION, OPENAPI_TAGS
from api.routes import API_ROUTERS
from api.spa import configure_spa

from learnwithai.config import Settings
from learnwithai.errors import AuthorizationError


def create_app(settings: Settings) -> FastAPI:
    """Creates and configures the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
    )

    @application.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        _request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    for router in API_ROUTERS:
        application.include_router(router, prefix="/api")

    configure_spa(application, settings)
    return application


settings = Settings()
app = create_app(settings)
