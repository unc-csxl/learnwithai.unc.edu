# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from learnwithai.config import Settings
from learnwithai.services.course_service import AuthorizationError

import api.lifespan as lifespan_module
from api.main import app, create_app, settings
from api.openapi import OPENAPI_TAGS


def _development_settings() -> Settings:
    return Settings.model_construct(
        _fields_set=None,
        environment="development",
        app_name="learnwithai",
    )


def test_app_uses_settings_app_name_for_title() -> None:
    # Arrange
    expected_title = settings.app_name

    # Act
    actual_title = app.title

    # Assert
    assert actual_title == expected_title


def test_app_registers_expected_routes() -> None:
    # Arrange
    dev_app = create_app(_development_settings())
    route_paths = {route.path for route in dev_app.routes if isinstance(route, APIRoute)}

    # Act
    has_health_route = "/api/health" in route_paths
    has_queue_route = "/api/queue" in route_paths
    has_auth_route = "/api/auth" in route_paths
    has_auth_me_route = "/api/me" in route_paths
    has_courses_route = "/api/courses" in route_paths
    has_roster_route = "/api/courses/{course_id}/roster" in route_paths
    has_members_route = "/api/courses/{course_id}/members" in route_paths
    has_drop_route = "/api/courses/{course_id}/members/{pid}" in route_paths
    has_dev_login_route = "/api/auth/as/{pid}" in route_paths
    has_dev_reset_route = "/api/dev/reset-db" in route_paths

    # Assert
    assert has_health_route is True
    assert has_queue_route is True
    assert has_auth_route is True
    assert has_auth_me_route is True
    assert has_courses_route is True
    assert has_roster_route is True
    assert has_members_route is True
    assert has_drop_route is True
    assert has_dev_login_route is True
    assert has_dev_reset_route is True


def test_app_excludes_dev_routes_in_production() -> None:
    # Arrange
    prod_settings = Settings.model_construct(_fields_set=None, environment="production", app_name="learnwithai")

    # Act
    prod_app = create_app(prod_settings)
    route_paths = {route.path for route in prod_app.routes if isinstance(route, APIRoute)}

    # Assert
    assert "/api/auth/as/{pid}" not in route_paths
    assert "/api/dev/reset-db" not in route_paths


def test_app_exposes_expected_openapi_tags() -> None:
    # Arrange
    expected_tag_names = {tag["name"] for tag in OPENAPI_TAGS}

    # Act
    actual_tag_names = {tag["name"] for tag in app.openapi()["tags"]}

    # Assert
    assert actual_tag_names == expected_tag_names


def test_app_assigns_tags_to_current_routes() -> None:
    # Arrange
    dev_app = create_app(_development_settings())
    openapi = dev_app.openapi()

    # Act
    health_tags = openapi["paths"]["/api/health"]["get"]["tags"]
    queue_tags = openapi["paths"]["/api/queue"]["post"]["tags"]
    auth_tags = openapi["paths"]["/api/auth"]["get"]["tags"]
    profile_tags = openapi["paths"]["/api/me"]["get"]["tags"]
    courses_list_tags = openapi["paths"]["/api/courses"]["get"]["tags"]
    courses_create_tags = openapi["paths"]["/api/courses"]["post"]["tags"]
    roster_tags = openapi["paths"]["/api/courses/{course_id}/roster"]["get"]["tags"]
    add_member_tags = openapi["paths"]["/api/courses/{course_id}/members"]["post"]["tags"]
    drop_member_tags = openapi["paths"]["/api/courses/{course_id}/members/{pid}"]["delete"]["tags"]
    dev_login_tags = openapi["paths"]["/api/auth/as/{pid}"]["get"]["tags"]
    dev_reset_tags = openapi["paths"]["/api/dev/reset-db"]["post"]["tags"]

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
    assert dev_login_tags == ["Development"]
    assert dev_reset_tags == ["Development"]


def test_operation_ids_use_function_names() -> None:
    """Operation IDs should be the Python function name, not the ugly default
    that includes the full URL path."""
    # Arrange
    openapi = app.openapi()
    operation_ids: list[str] = []
    for _path, methods in openapi["paths"].items():
        for _method, details in methods.items():
            if "operationId" in details:
                operation_ids.append(details["operationId"])

    # Assert — every ID should be a simple snake_case name without path fragments
    for op_id in operation_ids:
        assert "/api" not in op_id, f"operationId contains URL path: {op_id}"
        assert "__" not in op_id, f"operationId contains ugly separators: {op_id}"

    # Spot-check a few expected IDs
    assert "health" in operation_ids
    assert "create_course" in operation_ids
    assert "list_my_courses" in operation_ids
    assert "get_course_roster" in operation_ids


def test_lifespan_context_skips_consumer_in_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    async def fake_consume_job_updates(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(lifespan_module, "consume_job_updates", fake_consume_job_updates)
    monkeypatch.setattr(
        lifespan_module,
        "Settings",
        lambda: Settings.model_construct(
            _fields_set=None,
            environment="test",
            app_name="learnwithai",
        ),
    )

    async def exercise() -> None:
        lifespan = lifespan_module._lifespan_context(FastAPI())
        await anext(lifespan)
        with pytest.raises(StopAsyncIteration):
            await anext(lifespan)

    asyncio.run(exercise())

    assert called is False


def test_lifespan_context_starts_and_cancels_consumer_in_non_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def fake_consume_job_updates(*_args: object, **_kwargs: object) -> None:
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(lifespan_module, "consume_job_updates", fake_consume_job_updates)
    monkeypatch.setattr(
        lifespan_module,
        "Settings",
        lambda: Settings.model_construct(
            _fields_set=None,
            environment="development",
            app_name="learnwithai",
        ),
    )

    async def exercise() -> None:
        lifespan = lifespan_module._lifespan_context(FastAPI())
        await anext(lifespan)
        await asyncio.wait_for(started.wait(), timeout=1)
        with pytest.raises(StopAsyncIteration):
            await anext(lifespan)

    asyncio.run(exercise())

    assert started.is_set()
    assert cancelled.is_set()


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
