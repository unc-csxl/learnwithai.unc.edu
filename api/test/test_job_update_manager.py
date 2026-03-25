"""Tests for the JobUpdateManager."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from api.job_update_manager import JobUpdateManager
from learnwithai.interfaces.jobs import JobUpdate


def _make_update(
    *,
    job_id: int = 1,
    course_id: int = 10,
    user_id: int = 100,
    kind: str = "test",
    status: str = "completed",
) -> JobUpdate:
    return JobUpdate(job_id=job_id, course_id=course_id, user_id=user_id, kind=kind, status=status)


def _make_ws() -> AsyncMock:
    """Creates a mock WebSocket with an async send_text method."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestSubscribeUnsubscribe:
    def test_subscribe_adds_websocket(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)
        assert ws in manager._subscriptions[10]

    def test_unsubscribe_removes_websocket(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)
        manager.unsubscribe(10, ws)
        assert 10 not in manager._subscriptions

    def test_unsubscribe_nonexistent_is_safe(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.unsubscribe(10, ws)

    def test_unsubscribe_all_removes_from_every_course(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)
        manager.subscribe(20, ws)
        manager.unsubscribe_all(ws)
        assert 10 not in manager._subscriptions
        assert 20 not in manager._subscriptions


class TestBroadcast:
    def test_broadcast_sends_to_subscribed(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)

        update = _make_update(course_id=10)
        asyncio.run(manager.broadcast(update))

        ws.send_text.assert_called_once_with(update.model_dump_json())

    def test_broadcast_skips_other_courses(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(20, ws)

        update = _make_update(course_id=10)
        asyncio.run(manager.broadcast(update))

        ws.send_text.assert_not_called()

    def test_broadcast_removes_stale_connections(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        ws.send_text.side_effect = RuntimeError("connection closed")
        manager.subscribe(10, ws)

        update = _make_update(course_id=10)
        asyncio.run(manager.broadcast(update))

        assert 10 not in manager._subscriptions

    def test_broadcast_to_multiple_subscribers(self) -> None:
        manager = JobUpdateManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        manager.subscribe(10, ws1)
        manager.subscribe(10, ws2)

        update = _make_update(course_id=10)
        asyncio.run(manager.broadcast(update))

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()


class TestUnsubscribeBranches:
    def test_unsubscribe_keeps_other_subscribers(self) -> None:
        """When a course still has other subscribers after unsubscribe,
        the subscription set is retained (branch 50->exit)."""
        manager = JobUpdateManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        manager.subscribe(10, ws1)
        manager.subscribe(10, ws2)

        manager.unsubscribe(10, ws1)

        assert ws1 not in manager._subscriptions[10]
        assert ws2 in manager._subscriptions[10]

    def test_unsubscribe_all_keeps_other_websockets_courses(self) -> None:
        """When unsubscribe_all removes ws from one course but another
        course still has other subscribers (branch 64->62)."""
        manager = JobUpdateManager()
        ws_leaving = _make_ws()
        ws_staying = _make_ws()
        manager.subscribe(10, ws_leaving)
        manager.subscribe(10, ws_staying)
        manager.subscribe(20, ws_leaving)

        manager.unsubscribe_all(ws_leaving)

        # Course 10 still has ws_staying
        assert ws_staying in manager._subscriptions[10]
        # Course 20 was cleaned up (only ws_leaving was there)
        assert 20 not in manager._subscriptions
