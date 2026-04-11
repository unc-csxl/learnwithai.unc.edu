# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from learnwithai.rabbitmq_management import DEFAULT_VHOST, RabbitMQManagementClient


@pytest.fixture
def client() -> RabbitMQManagementClient:
    return RabbitMQManagementClient(
        base_url="http://rabbitmq:15672",
        username="guest",
        password="guest",
    )


def _mock_response(json_data: Any, status_code: int = 200) -> MagicMock:
    """Builds a fake httpx.Response with the given JSON payload."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    return response


class TestGetOverview:
    def test_returns_overview_dict(self, client: RabbitMQManagementClient) -> None:
        overview = {"cluster_name": "rabbit@test", "node": "rabbit@test"}
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http.get.return_value = _mock_response(overview)

            result = client.get_overview()

        assert result == overview
        mock_http.get.assert_called_once_with("http://rabbitmq:15672/api/overview")

    def test_raises_on_http_error(self, client: RabbitMQManagementClient) -> None:
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            bad_response = _mock_response({}, status_code=500)
            bad_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=bad_response,
            )
            mock_http.get.return_value = bad_response

            with pytest.raises(httpx.HTTPStatusError):
                client.get_overview()


class TestGetQueues:
    def test_returns_queue_list(self, client: RabbitMQManagementClient) -> None:
        queues = [{"name": "default", "messages": 5}]
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http.get.return_value = _mock_response(queues)

            result = client.get_queues()

        assert result == queues
        mock_http.get.assert_called_once_with(f"http://rabbitmq:15672/api/queues/{DEFAULT_VHOST}")

    def test_custom_vhost(self, client: RabbitMQManagementClient) -> None:
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http.get.return_value = _mock_response([])

            client.get_queues(vhost="test-vhost")

        mock_http.get.assert_called_once_with("http://rabbitmq:15672/api/queues/test-vhost")


class TestGetConsumers:
    def test_returns_consumer_list(self, client: RabbitMQManagementClient) -> None:
        consumers = [{"consumer_tag": "worker.1"}]
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http.get.return_value = _mock_response(consumers)

            result = client.get_consumers()

        assert result == consumers
        mock_http.get.assert_called_once_with(f"http://rabbitmq:15672/api/consumers/{DEFAULT_VHOST}")


class TestPurgeQueue:
    def test_sends_delete_request(self, client: RabbitMQManagementClient) -> None:
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http.delete.return_value = _mock_response(None, status_code=204)

            client.purge_queue("default")

        mock_http.delete.assert_called_once_with(f"http://rabbitmq:15672/api/queues/{DEFAULT_VHOST}/default/contents")

    def test_raises_on_purge_failure(self, client: RabbitMQManagementClient) -> None:
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            bad_response = _mock_response(None, status_code=404)
            bad_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=bad_response,
            )
            mock_http.delete.return_value = bad_response

            with pytest.raises(httpx.HTTPStatusError):
                client.purge_queue("nonexistent")


class TestBaseUrlNormalization:
    def test_trailing_slash_stripped(self) -> None:
        c = RabbitMQManagementClient("http://host:15672/", "u", "p")
        with patch("learnwithai.rabbitmq_management.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_http.get.return_value = _mock_response({})

            c.get_overview()

        mock_http.get.assert_called_once_with("http://host:15672/api/overview")
