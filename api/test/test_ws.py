# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the WebSocket job updates endpoint."""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.realtime.manager import JobUpdateManager
from api.routes import ws as ws_route_module


@pytest.fixture(autouse=True)
def _configure_manager() -> Iterator[None]:
    """Ensures the WS module has a manager configured for each test."""
    manager = JobUpdateManager()
    ws_route_module.configure(manager)
    yield
    ws_route_module._manager = None


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _valid_token() -> str:
    """Issues a real JWT from the app's default test settings."""
    from learnwithai.config import Settings

    settings = Settings()
    from datetime import datetime, timedelta, timezone

    import jwt as pyjwt

    payload = {
        "sub": "999999999",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return pyjwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class TestGetManager:
    def test_raises_when_not_configured(self) -> None:
        ws_route_module._manager = None
        with pytest.raises(RuntimeError, match="not configured"):
            ws_route_module._get_manager()


class TestWebSocketAuth:
    def test_rejects_missing_token(self, client: TestClient) -> None:
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/jobs"):
                pass

    def test_rejects_invalid_token(self, client: TestClient) -> None:
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/jobs?token=bogus"):
                pass

    def test_accepts_valid_token(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text(json.dumps({"action": "subscribe", "course_id": 1}))
            data = json.loads(ws.receive_text())
            assert data["status"] == "subscribed"


class TestWebSocketMessages:
    def test_subscribe_returns_confirmation(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text(json.dumps({"action": "subscribe", "course_id": 42}))
            data = json.loads(ws.receive_text())
            assert data == {"status": "subscribed", "course_id": 42}

    def test_unsubscribe_returns_confirmation(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text(json.dumps({"action": "subscribe", "course_id": 42}))
            ws.receive_text()
            ws.send_text(json.dumps({"action": "unsubscribe", "course_id": 42}))
            data = json.loads(ws.receive_text())
            assert data == {"status": "unsubscribed", "course_id": 42}

    def test_invalid_json_returns_error(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text("not json at all")
            data = json.loads(ws.receive_text())
            assert data == {"error": "Invalid JSON."}

    def test_unknown_action_returns_error(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text(json.dumps({"action": "dance", "course_id": 1}))
            data = json.loads(ws.receive_text())
            assert data == {"error": "Unknown action."}

    def test_missing_course_id_returns_error(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text(json.dumps({"action": "subscribe"}))
            data = json.loads(ws.receive_text())
            assert data == {"error": "course_id must be an integer."}

    def test_non_integer_course_id_returns_error(self, client: TestClient) -> None:
        token = _valid_token()
        with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
            ws.send_text(json.dumps({"action": "subscribe", "course_id": "abc"}))
            data = json.loads(ws.receive_text())
            assert data == {"error": "course_id must be an integer."}


class TestConnectionIdentity:
    def test_manager_registers_user_id_on_connect(self) -> None:
        """After accepting a connection, the manager records the user's pid."""
        token = _valid_token()

        with TestClient(app) as client:
            manager = ws_route_module._get_manager()
            with client.websocket_connect(f"/api/ws/jobs?token={token}") as ws:
                ws.send_text(json.dumps({"action": "subscribe", "course_id": 1}))
                ws.receive_text()
                # Inside the context, the connection is registered
                assert len(manager._connection_user) == 1
                user_id = next(iter(manager._connection_user.values()))
                assert user_id == 999999999  # sub from _valid_token

        # After disconnect, identity is cleared
        assert len(manager._connection_user) == 0
