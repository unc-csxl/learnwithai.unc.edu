"""WebSocket endpoint for real-time job update delivery.

Clients connect with a JWT in the query string and subscribe to updates
for specific courses by sending JSON ``subscribe``/``unsubscribe``
messages.  Updates are pushed to clients from the
:class:`~api.job_update_manager.JobUpdateManager`.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from learnwithai.config import Settings
from learnwithai.services.csxl_auth_service import AuthenticationException

from api.job_update_manager import JobUpdateManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton manager — assigned at application startup via ``configure()``.
_manager: JobUpdateManager | None = None


def configure(manager: JobUpdateManager) -> None:
    """Links the module-level manager used by the WebSocket endpoint.

    Must be called once during application startup before any connections
    are accepted.

    Args:
        manager: The shared subscription manager for this process.
    """
    global _manager
    _manager = manager


@router.websocket("/ws/jobs")
async def job_updates_ws(websocket: WebSocket, token: str = "") -> None:
    """WebSocket endpoint that streams job updates to authenticated clients.

    Query Parameters:
        token: A valid JWT issued by the application auth flow.

    Client Messages (JSON):
        ``{"action": "subscribe", "course_id": 123}``
        ``{"action": "unsubscribe", "course_id": 123}``

    Server Messages (JSON):
        ``JobUpdate`` objects serialized as JSON whenever a subscribed
        course's job changes status.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = _authenticate_token(token)
    except AuthenticationException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager = _get_manager()
    await websocket.accept()
    manager.register_connection(websocket, user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON."}))
                continue

            action = message.get("action")
            course_id = message.get("course_id")

            if action not in ("subscribe", "unsubscribe"):
                await websocket.send_text(json.dumps({"error": "Unknown action."}))
                continue

            if not isinstance(course_id, int):
                await websocket.send_text(
                    json.dumps({"error": "course_id must be an integer."})
                )
                continue

            if action == "subscribe":
                manager.subscribe(course_id, websocket)
                await websocket.send_text(
                    json.dumps({"status": "subscribed", "course_id": course_id})
                )
            else:
                manager.unsubscribe(course_id, websocket)
                await websocket.send_text(
                    json.dumps({"status": "unsubscribed", "course_id": course_id})
                )
    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe_all(websocket)


def _get_manager() -> JobUpdateManager:
    """Returns the configured manager, raising if not yet set."""
    if _manager is None:
        raise RuntimeError(
            "JobUpdateManager not configured. Call configure() at startup."
        )
    return _manager


def _authenticate_token(token: str) -> int:
    """Validates a JWT and returns the user PID.

    Args:
        token: JWT from the query string.

    Returns:
        The user PID encoded in the token.

    Raises:
        AuthenticationException: If the token is invalid or expired.
    """
    settings = Settings()
    import jwt as pyjwt

    try:
        payload = pyjwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return int(payload["sub"])
    except (pyjwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AuthenticationException() from exc
