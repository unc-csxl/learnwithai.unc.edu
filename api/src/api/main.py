"""Application entrypoint for the FastAPI adapter."""

from fastapi import FastAPI

from api.openapi import API_DESCRIPTION, OPENAPI_TAGS
from api.routes import API_ROUTERS
from api.spa import configure_spa

from learnwithai.config import Settings


def create_app(settings: Settings) -> FastAPI:
    """Creates and configures the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
    )

    for router in API_ROUTERS:
        application.include_router(router, prefix="/api")

    configure_spa(application, settings)
    return application


settings = Settings()
app = create_app(settings)
