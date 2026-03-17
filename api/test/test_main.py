from __future__ import annotations

from fastapi.routing import APIRoute

from api.main import app, settings
from api.openapi import OPENAPI_TAGS


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

    # Assert
    assert has_health_route is True
    assert has_queue_route is True
    assert has_auth_route is True
    assert has_auth_me_route is True


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

    # Assert
    assert health_tags == ["Operations"]
    assert queue_tags == ["Operations"]
    assert auth_tags == ["Authentication"]
    assert profile_tags == ["Authentication"]
