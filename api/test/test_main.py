from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from api.dependency_injection import (
    course_repository_factory,
    course_service_factory,
    membership_repository_factory,
)
from api.main import app, settings
from api.openapi import OPENAPI_TAGS
from learnwithai.services.course_service import AuthorizationError


def test_app_uses_settings_app_name_for_title() -> None:
    # Arrange
    expected_title = settings.app_name

    # Act
    actual_title = app.title

    # Assert
    assert actual_title == expected_title


def test_app_registers_expected_routes() -> None:
    # Arrange
    route_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}

    # Act
    has_health_route = "/api/health" in route_paths
    has_queue_route = "/api/queue" in route_paths
    has_auth_route = "/api/auth" in route_paths
    has_auth_me_route = "/api/me" in route_paths
    has_courses_route = "/api/courses" in route_paths
    has_roster_route = "/api/courses/{course_id}/roster" in route_paths
    has_members_route = "/api/courses/{course_id}/members" in route_paths
    has_drop_route = "/api/courses/{course_id}/members/{pid}" in route_paths

    # Assert
    assert has_health_route is True
    assert has_queue_route is True
    assert has_auth_route is True
    assert has_auth_me_route is True
    assert has_courses_route is True
    assert has_roster_route is True
    assert has_members_route is True
    assert has_drop_route is True


def test_app_exposes_expected_openapi_tags() -> None:
    # Arrange
    expected_tag_names = {tag["name"] for tag in OPENAPI_TAGS}

    # Act
    actual_tag_names = {tag["name"] for tag in app.openapi()["tags"]}

    # Assert
    assert actual_tag_names == expected_tag_names


def test_app_assigns_tags_to_current_routes() -> None:
    # Arrange
    openapi = app.openapi()

    # Act
    health_tags = openapi["paths"]["/api/health"]["get"]["tags"]
    queue_tags = openapi["paths"]["/api/queue"]["post"]["tags"]
    auth_tags = openapi["paths"]["/api/auth"]["get"]["tags"]
    profile_tags = openapi["paths"]["/api/me"]["get"]["tags"]
    courses_list_tags = openapi["paths"]["/api/courses"]["get"]["tags"]
    courses_create_tags = openapi["paths"]["/api/courses"]["post"]["tags"]
    roster_tags = openapi["paths"]["/api/courses/{course_id}/roster"]["get"]["tags"]
    add_member_tags = openapi["paths"]["/api/courses/{course_id}/members"]["post"][
        "tags"
    ]
    drop_member_tags = openapi["paths"]["/api/courses/{course_id}/members/{pid}"][
        "delete"
    ]["tags"]

    # Assert
    assert health_tags == ["Operations"]
    assert queue_tags == ["Operations"]
    assert auth_tags == ["Authentication"]
    assert profile_tags == ["Authentication"]
    assert courses_list_tags == ["Courses"]
    assert courses_create_tags == ["Courses"]
    assert roster_tags == ["Courses"]
    assert add_member_tags == ["Courses"]
    assert drop_member_tags == ["Courses"]


# ---- DI factories ----


def test_course_repository_factory_returns_repository() -> None:
    # Arrange
    session = MagicMock()

    # Act
    repo = course_repository_factory(session)

    # Assert
    assert repo._session is session


def test_membership_repository_factory_returns_repository() -> None:
    # Arrange
    session = MagicMock()

    # Act
    repo = membership_repository_factory(session)

    # Assert
    assert repo._session is session


def test_course_service_factory_returns_service() -> None:
    # Arrange
    course_repo = MagicMock()
    membership_repo = MagicMock()

    # Act
    svc = course_service_factory(course_repo, membership_repo)

    # Assert
    assert svc._course_repo is course_repo
    assert svc._membership_repo is membership_repo


# ---- exception handler ----


@pytest.mark.integration
def test_authorization_error_returns_403(client: TestClient) -> None:
    """Raises AuthorizationError in a real handler and checks for 403."""
    # Arrange — temporarily add a route that raises AuthorizationError
    from fastapi import APIRouter

    test_router = APIRouter()

    @test_router.get("/_test_authz")
    def _trigger_authz_error() -> None:
        raise AuthorizationError("forbidden")

    app.include_router(test_router, prefix="/api")

    # Act
    response = client.get("/api/_test_authz")

    # Assert
    assert response.status_code == 403
    assert response.json() == {"detail": "forbidden"}

    # Cleanup — remove the test route
    app.routes[:] = [
        r
        for r in app.routes
        if not (hasattr(r, "path") and r.path == "/api/_test_authz")  # type: ignore[union-attr]
    ]
