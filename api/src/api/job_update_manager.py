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

    def register_connection(self, websocket: WebSocket, user_id: int) -> None:
        """Records the authenticated user identity for a connected socket.

        Must be called immediately after the WebSocket is accepted so
        that :meth:`broadcast` can filter updates by owner.

        Args:
            websocket: The accepted WebSocket connection.
            user_id: The ``pid`` of the authenticated user.
        """
        self._connection_user[websocket] = user_id

    def unregister_connection(self, websocket: WebSocket) -> None:
        """Removes the identity record when a connection closes.

        Args:
            websocket: The closing WebSocket connection.
        """
        self._connection_user.pop(websocket, None)

    def subscribe(self, course_id: int, websocket: WebSocket) -> None:
        """Registers a WebSocket to receive updates for a course.

        Args:
            course_id: The course whose job updates the client wants.
            websocket: The connected WebSocket client.
        """
        self._subscriptions[course_id].add(websocket)

    def unsubscribe(self, course_id: int, websocket: WebSocket) -> None:
        """Removes a WebSocket from a course's subscription set.

        Args:
            course_id: The course the client was subscribed to.
            websocket: The WebSocket to remove.
        """
        subscribers = self._subscriptions.get(course_id)
        if subscribers is not None:
            subscribers.discard(websocket)
            if not subscribers:
                del self._subscriptions[course_id]

    def unsubscribe_all(self, websocket: WebSocket) -> None:
        """Removes a WebSocket from every course subscription and clears its identity.

        Called when a connection closes so stale references are cleaned up.

        Args:
            websocket: The disconnected WebSocket.
        """
        empty_courses: list[int] = []
        for course_id, subscribers in self._subscriptions.items():
            subscribers.discard(websocket)
            if not subscribers:
                empty_courses.append(course_id)
        for course_id in empty_courses:
            del self._subscriptions[course_id]
        self.unregister_connection(websocket)

    async def broadcast(self, update: JobUpdate) -> None:
        """Sends a job update only to WebSockets owned by the job's user.

        Each connection has a registered ``user_id`` set at accept time.
        The update is delivered only to connections whose identity matches
        ``update.user_id``, preventing one user from observing another's
        job outcomes.  Broken connections are silently removed.

        Args:
            update: The job status change to distribute.
        """
        subscribers = self._subscriptions.get(update.course_id)
        if not subscribers:
            return

        payload = update.model_dump_json()
        stale: list[WebSocket] = []

        send_tasks = [
            self._safe_send(ws, payload, stale)
            for ws in subscribers
            if self._connection_user.get(ws) == update.user_id
        ]
        await asyncio.gather(*send_tasks)

        for ws in stale:
            subscribers.discard(ws)
        if not subscribers:
            del self._subscriptions[update.course_id]

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
