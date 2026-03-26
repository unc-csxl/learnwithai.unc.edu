"""OpenAPI metadata and customization for the LearnWithAI API."""

from fastapi.routing import APIRoute


def generate_operation_id(route: APIRoute) -> str:
    """Uses the Python function name as the OpenAPI operationId.

    FastAPI's default includes the full URL path, which produces unwieldy
    names in generated clients (e.g. ``create_course_api_courses_post``).
    This override yields clean identifiers like ``create_course``.
    """
    return route.name


API_DESCRIPTION = (
    "HTTP API for LearnWithAI, including operational endpoints, UNC "
    "authentication flows, and authenticated user profile access."
)

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "Operations",
        "description": "Health checks and operational endpoints for the service.",
    },
    {
        "name": "Authentication",
        "description": (
            "Authentication redirects, callback handling, and authenticated "
            "identity endpoints."
        ),
    },
    {
        "name": "Courses",
        "description": ("Course management, enrollment, and roster endpoints."),
    },
    {
        "name": "Development",
        "description": (
            "Routes available only in the development environment for local "
            "testing and database management."
        ),
    },
    {
        "name": "Instructor Tools",
        "description": "AI-powered instructor tools including joke generation.",
    },
]
