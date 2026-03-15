from fastapi import FastAPI

from api.routes.health import router as health_router
from learnwithai.config import Settings

settings = Settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
