"""Application entrypoint for the FastAPI adapter."""

from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.auth import router as auth_router

from learnwithai.config import Settings

settings = Settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(auth_router, prefix="/auth")
