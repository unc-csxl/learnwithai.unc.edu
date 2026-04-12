# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Thin HTTP client for the RabbitMQ Management API."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_VHOST = "%2F"


class RabbitMQManagementClient:
    """Wraps the RabbitMQ Management HTTP API.

    Uses ``httpx`` to query the management plugin endpoints for queue
    statistics, consumer information, and administrative actions like
    purging a queue.

    Args:
        base_url: Root URL of the RabbitMQ Management API
            (e.g. ``http://rabbitmq:15672``).
        username: Management API username.
        password: Management API password.
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = httpx.BasicAuth(username, password)

    def get_overview(self) -> dict[str, Any]:
        """Returns the broker overview including cluster name and alarms.

        Returns:
            Parsed JSON response from ``GET /api/overview``.
        """
        return self._get("/api/overview")

    def get_queues(self, vhost: str = DEFAULT_VHOST) -> list[dict[str, Any]]:
        """Returns queue statistics for the given virtual host.

        Args:
            vhost: URL-encoded virtual host name (defaults to ``%2F``).

        Returns:
            List of queue info dicts from ``GET /api/queues/{vhost}``.
        """
        return self._get(f"/api/queues/{vhost}")

    def get_consumers(self, vhost: str = DEFAULT_VHOST) -> list[dict[str, Any]]:
        """Returns active consumers for the given virtual host.

        Args:
            vhost: URL-encoded virtual host name (defaults to ``%2F``).

        Returns:
            List of consumer info dicts from ``GET /api/consumers/{vhost}``.
        """
        return self._get(f"/api/consumers/{vhost}")

    def peek_queue_messages(
        self,
        queue_name: str,
        *,
        count: int = 5,
        vhost: str = DEFAULT_VHOST,
        truncate: int = 5_000,
    ) -> list[dict[str, Any]]:
        """Returns a non-destructive preview of messages waiting in a queue.

        Args:
            queue_name: Name of the queue to inspect.
            count: Maximum number of messages to preview.
            vhost: URL-encoded virtual host name (defaults to ``%2F``).
            truncate: Maximum payload size returned by RabbitMQ.

        Returns:
            List of preview message dicts from ``POST /api/queues/{vhost}/{queue}/get``.
        """
        url = f"{self._base_url}/api/queues/{vhost}/{queue_name}/get"
        payload = {
            "count": count,
            "ackmode": "ack_requeue_true",
            "encoding": "auto",
            "truncate": truncate,
        }
        with httpx.Client(auth=self._auth, timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    def purge_queue(self, queue_name: str, vhost: str = DEFAULT_VHOST) -> None:
        """Purges all messages from the specified queue.

        Args:
            queue_name: Name of the queue to purge.
            vhost: URL-encoded virtual host name (defaults to ``%2F``).
        """
        url = f"{self._base_url}/api/queues/{vhost}/{queue_name}/contents"
        with httpx.Client(auth=self._auth, timeout=10.0) as client:
            response = client.delete(url)
            response.raise_for_status()

    def _get(self, path: str) -> Any:
        """Performs an authenticated GET request and returns parsed JSON.

        Args:
            path: API path relative to the base URL.

        Returns:
            Parsed JSON response body.
        """
        url = f"{self._base_url}{path}"
        with httpx.Client(auth=self._auth, timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
