from __future__ import annotations

from fastapi.routing import APIRoute

from api.main import app, settings


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
    has_health_route = "/health" in route_paths
    has_queue_route = "/queue" in route_paths

    # Assert
    assert has_health_route is True
    assert has_queue_route is True
