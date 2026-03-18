from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.dependency_injection import job_queue_factory
from api.main import app
from api.routes.health import health, queue


def test_health_route_function_returns_health_status() -> None:
    # Arrange
    expected_status = {"status": "ok", "app": "learnwithai", "environment": "test"}

    # Act
    with patch("api.routes.health.get_health_status", return_value=expected_status):
        response = health()

    # Assert
    assert response == expected_status


def test_queue_route_function_enqueues_echo_job() -> None:
    # Arrange
    job_queue = Mock()

    # Act
    response = queue(job_queue)

    # Assert
    assert response == "ok"
    job_queue.enqueue.assert_called_once()
    enqueued_job = job_queue.enqueue.call_args.args[0]
    assert enqueued_job.type == "echo"
    assert enqueued_job.message == "hello"


@pytest.mark.integration
def test_health_endpoint_returns_json_payload(client: TestClient) -> None:
    # Arrange
    expected_status = {"status": "ok", "app": "api-test", "environment": "test"}

    # Act
    with patch("api.routes.health.get_health_status", return_value=expected_status):
        response = client.get("/api/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_status


@pytest.mark.integration
def test_queue_endpoint_uses_dependency_overrides(client: TestClient) -> None:
    # Arrange
    job_queue = Mock()
    app.dependency_overrides[job_queue_factory] = lambda: job_queue

    # Act
    response = client.post("/api/queue")

    # Assert
    assert response.status_code == 200
    assert response.json() == "ok"
    job_queue.enqueue.assert_called_once()
