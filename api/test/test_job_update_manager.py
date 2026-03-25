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
    return JobUpdate(
        job_id=job_id, course_id=course_id, user_id=user_id, kind=kind, status=status
    )


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

    def test_unsubscribe_nonexistent_is_safe_with_registered_identity(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.unsubscribe(10, ws)

    def test_unsubscribe_all_removes_from_every_course(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)
        manager.subscribe(20, ws)
        manager.unsubscribe_all(ws)
        assert 10 not in manager._subscriptions
        assert 20 not in manager._subscriptions

    def test_unsubscribe_all_clears_connection_identity(self) -> None:
        """After unsubscribe_all, the identity record for the socket is removed."""
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)

        manager.unsubscribe_all(ws)

        assert ws not in manager._connection_user
        assert (100, 10) not in manager._user_subscriptions

    def test_register_and_unregister_connection(self) -> None:
        """register_connection stores user_id; unregister_connection removes it."""
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 42)
        assert manager._connection_user[ws] == 42

        manager.unregister_connection(ws)
        assert ws not in manager._connection_user

    def test_register_connection_reindexes_existing_subscriptions(self) -> None:
        """Re-registering a socket under a different user updates the index."""
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)

        manager.register_connection(ws, 200)

        assert (100, 10) not in manager._user_subscriptions
        assert ws in manager._user_subscriptions[(200, 10)]

    def test_unregister_connection_removes_existing_index_entries(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)

        manager.unregister_connection(ws)

        assert ws not in manager._connection_user
        assert (100, 10) not in manager._user_subscriptions

    def test_unregister_connection_is_safe_for_unknown_socket(self) -> None:
        """unregister_connection does not raise for a socket that was never registered."""
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.unregister_connection(ws)  # should not raise


class TestBroadcast:
    def test_broadcast_sends_to_subscribed(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)

        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))

        ws.send_text.assert_called_once_with(update.model_dump_json())

    def test_broadcast_skips_other_courses(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(20, ws)

        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))

        ws.send_text.assert_not_called()

    def test_broadcast_removes_stale_connections(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        ws.send_text.side_effect = RuntimeError("connection closed")
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)
        manager.subscribe(20, ws)

        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))

        assert 10 not in manager._subscriptions
        assert 20 not in manager._subscriptions
        assert (100, 10) not in manager._user_subscriptions
        assert (100, 20) not in manager._user_subscriptions
        assert ws not in manager._connection_user

    def test_broadcast_to_multiple_subscribers(self) -> None:
        manager = JobUpdateManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        manager.register_connection(ws1, 100)
        manager.register_connection(ws2, 100)
        manager.subscribe(10, ws1)
        manager.subscribe(10, ws2)

        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    def test_broadcast_does_not_reach_other_users(self) -> None:
        """A socket registered as user B does not receive updates for user A."""
        manager = JobUpdateManager()
        ws_a = _make_ws()
        ws_b = _make_ws()
        manager.register_connection(ws_a, 100)
        manager.register_connection(ws_b, 200)
        manager.subscribe(10, ws_a)
        manager.subscribe(10, ws_b)

        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))

        ws_a.send_text.assert_called_once()
        ws_b.send_text.assert_not_called()

    def test_broadcast_skips_unregistered_connections(self) -> None:
        """Connections without a registered identity never receive updates."""
        manager = JobUpdateManager()
        ws = _make_ws()
        # Deliberately omit register_connection
        manager.subscribe(10, ws)

        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))

        ws.send_text.assert_not_called()

    def test_broadcast_no_subscribers_returns_early(self) -> None:
        """No exception when broadcast is called with no subscribers."""
        manager = JobUpdateManager()
        update = _make_update(course_id=10, user_id=100)
        asyncio.run(manager.broadcast(update))  # should not raise


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

    def test_unsubscribe_keeps_index_when_other_same_user_socket_remains(self) -> None:
        manager = JobUpdateManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        manager.register_connection(ws1, 100)
        manager.register_connection(ws2, 100)
        manager.subscribe(10, ws1)
        manager.subscribe(10, ws2)

        manager.unsubscribe(10, ws1)

        assert (100, 10) in manager._user_subscriptions
        assert ws1 not in manager._user_subscriptions[(100, 10)]
        assert ws2 in manager._user_subscriptions[(100, 10)]

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


class TestUserSubscriptionsIndex:
    """Covers the (user_id, course_id) secondary index used for O(1) broadcast."""

    def test_subscribe_adds_to_index_when_registered(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)
        assert ws in manager._user_subscriptions[(100, 10)]

    def test_subscribe_skips_index_when_unregistered(self) -> None:
        """A socket subscribed before register_connection is not indexed."""
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)
        assert (100, 10) not in manager._user_subscriptions

    def test_register_connection_backfills_existing_subscriptions(self) -> None:
        """Late identity registration indexes any subscriptions already in place."""
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.subscribe(10, ws)

        manager.register_connection(ws, 100)

        assert ws in manager._user_subscriptions[(100, 10)]

    def test_unsubscribe_removes_from_index(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)
        manager.unsubscribe(10, ws)
        assert (100, 10) not in manager._user_subscriptions

    def test_unsubscribe_all_clears_index_for_all_courses(self) -> None:
        manager = JobUpdateManager()
        ws = _make_ws()
        manager.register_connection(ws, 100)
        manager.subscribe(10, ws)
        manager.subscribe(20, ws)
        manager.unsubscribe_all(ws)
        assert (100, 10) not in manager._user_subscriptions
        assert (100, 20) not in manager._user_subscriptions

    def test_broadcast_uses_direct_index_skips_other_user_sockets(self) -> None:
        """With 200 course subscribers, broadcast reaches only the target user."""
        manager = JobUpdateManager()
        target = _make_ws()
        manager.register_connection(target, 42)
        manager.subscribe(10, target)

        # 199 other users in the same course
        for uid in range(1, 200):
            other = _make_ws()
            manager.register_connection(other, uid)
            manager.subscribe(10, other)

        update = _make_update(course_id=10, user_id=42)
        asyncio.run(manager.broadcast(update))

        target.send_text.assert_called_once_with(update.model_dump_json())
