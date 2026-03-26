"""In-memory WebSocket subscription manager for real-time job updates.

Tracks which WebSocket connections are interested in updates for a given
course.  When a job update arrives (from the RabbitMQ consumer), the
manager fans it out to every WebSocket subscribed to that course.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket
from learnwithai.interfaces.jobs import JobUpdate

logger = logging.getLogger(__name__)


class JobUpdateManager:
    """Manages a mapping from course IDs to connected WebSocket clients.

    Thread safety is not required because all methods are called from
    the same ``asyncio`` event loop.
    """

    def __init__(self) -> None:
        self._subscriptions: defaultdict[int, set[WebSocket]] = defaultdict(set)
        self._connection_user: dict[WebSocket, int] = {}
        # Secondary index keyed by (user_id, course_id) so broadcast can
        # locate exactly the sockets it needs in O(1) rather than scanning
        # every subscriber in the course.
        self._user_subscriptions: defaultdict[tuple[int, int], set[WebSocket]] = defaultdict(set)

    def register_connection(self, websocket: WebSocket, user_id: int) -> None:
        """Records the authenticated user identity for a connected socket.

        Must be called immediately after the WebSocket is accepted so
        that :meth:`broadcast` can filter updates by owner.

        Args:
            websocket: The accepted WebSocket connection.
            user_id: The ``pid`` of the authenticated user.
        """
        previous_user_id = self._connection_user.get(websocket)
        if previous_user_id is not None and previous_user_id != user_id:
            for course_id in self._subscribed_course_ids(websocket):
                self._discard_index_entry(previous_user_id, course_id, websocket)

        self._connection_user[websocket] = user_id

        for course_id in self._subscribed_course_ids(websocket):
            self._index_subscription(user_id, course_id, websocket)

    def unregister_connection(self, websocket: WebSocket) -> None:
        """Removes the identity record when a connection closes.

        Args:
            websocket: The closing WebSocket connection.
        """
        user_id = self._connection_user.pop(websocket, None)
        if user_id is None:
            return

        for course_id in self._subscribed_course_ids(websocket):
            self._discard_index_entry(user_id, course_id, websocket)

    def subscribe(self, course_id: int, websocket: WebSocket) -> None:
        """Registers a WebSocket to receive updates for a course.

        Also updates the ``(user_id, course_id)`` secondary index when the
        connection has already been registered via :meth:`register_connection`.

        Args:
            course_id: The course whose job updates the client wants.
            websocket: The connected WebSocket client.
        """
        self._subscriptions[course_id].add(websocket)
        user_id = self._connection_user.get(websocket)
        if user_id is not None:
            self._index_subscription(user_id, course_id, websocket)

    def unsubscribe(self, course_id: int, websocket: WebSocket) -> None:
        """Removes a WebSocket from a course's subscription set.

        Also removes the entry from the ``(user_id, course_id)`` secondary
        index.

        Args:
            course_id: The course the client was subscribed to.
            websocket: The WebSocket to remove.
        """
        subscribers = self._subscriptions.get(course_id)
        if subscribers is not None:
            subscribers.discard(websocket)
            if not subscribers:
                del self._subscriptions[course_id]

        user_id = self._connection_user.get(websocket)
        if user_id is not None:
            self._discard_index_entry(user_id, course_id, websocket)

    def unsubscribe_all(self, websocket: WebSocket) -> None:
        """Removes a WebSocket from every course subscription and clears its identity.

        Called when a connection closes so stale references are cleaned up.

        Args:
            websocket: The disconnected WebSocket.
        """
        subscribed_course_ids = self._subscribed_course_ids(websocket)
        for course_id in subscribed_course_ids:
            self.unsubscribe(course_id, websocket)

        self.unregister_connection(websocket)

    async def broadcast(self, update: JobUpdate) -> None:
        """Sends a job update only to WebSockets owned by the job's user.

        Uses the ``(user_id, course_id)`` secondary index for an O(1) lookup
        so that delivery cost scales with the number of open tabs owned by
        the target user — not with the total number of course subscribers.
        Broken connections are silently removed from both indexes.

        Args:
            update: The job status change to distribute.
        """
        key = (update.user_id, update.course_id)
        subscribers = self._user_subscriptions.get(key)
        if not subscribers:
            return

        payload = update.model_dump_json()
        stale: list[WebSocket] = []

        send_tasks = [self._safe_send(ws, payload, stale) for ws in tuple(subscribers)]
        await asyncio.gather(*send_tasks)

        for ws in stale:
            self.unsubscribe_all(ws)

    def _index_subscription(self, user_id: int, course_id: int, websocket: WebSocket) -> None:
        """Adds a socket to the direct-lookup ``(user_id, course_id)`` index."""
        self._user_subscriptions[(user_id, course_id)].add(websocket)

    def _discard_index_entry(self, user_id: int, course_id: int, websocket: WebSocket) -> None:
        """Removes a socket from the direct-lookup ``(user_id, course_id)`` index."""
        key = (user_id, course_id)
        subscribers = self._user_subscriptions.get(key)
        if subscribers is None:
            return

        subscribers.discard(websocket)
        if not subscribers:
            del self._user_subscriptions[key]

    def _subscribed_course_ids(self, websocket: WebSocket) -> list[int]:
        """Returns all course IDs that currently include this socket.

        Membership checks use object identity instead of ``in`` because the
        tests use ``AsyncMock`` sockets whose equality semantics are looser
        than real ``WebSocket`` objects.
        """
        return [
            course_id
            for course_id, subscribers in self._subscriptions.items()
            if any(subscriber is websocket for subscriber in subscribers)
        ]

    @staticmethod
    async def _safe_send(ws: WebSocket, payload: str, stale: list[WebSocket]) -> None:
        """Sends text to a single WebSocket, marking it stale on failure.

        Args:
            ws: The target WebSocket.
            payload: JSON string to send.
            stale: Accumulator for connections that failed to receive.
        """
        try:
            await ws.send_text(payload)
        except Exception:
            stale.append(ws)
