"""OpenAPI metadata for the LearnWithAI API."""

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
]
