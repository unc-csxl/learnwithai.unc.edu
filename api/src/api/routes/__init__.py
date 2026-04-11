# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Route exports for the FastAPI application."""

from api.routes.activities import router as activities_router
from api.routes.auth import router as auth_router
from api.routes.courses import router as courses_router
from api.routes.health import router as health_router
from api.routes.joke_generation import router as joke_generation_router
from api.routes.me import router as me_router
from api.routes.operations import router as operations_router
from api.routes.roster_uploads import router as roster_uploads_router

API_ROUTERS = (
    health_router,
    auth_router,
    me_router,
    courses_router,
    activities_router,
    roster_uploads_router,
    joke_generation_router,
    operations_router,
)

__all__ = ["API_ROUTERS"]
