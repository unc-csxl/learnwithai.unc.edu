from learnwithai.config import Settings


def get_health_status() -> dict[str, str]:
    settings = Settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
