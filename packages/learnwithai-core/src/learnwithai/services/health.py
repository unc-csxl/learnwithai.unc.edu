# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Health helpers shared across services."""

from learnwithai.config import Settings


def get_health_status() -> dict[str, str]:
    """Builds a health payload for the running service."""
    settings = Settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
