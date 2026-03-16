from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from learnwithai.services.health import get_health_status


def test_get_health_status_returns_expected_payload() -> None:
    # Arrange
    mocked_settings = SimpleNamespace(app_name="test-app", environment="test")

    # Act
    with patch("learnwithai.services.health.Settings", return_value=mocked_settings):
        health_status = get_health_status()

    # Assert
    assert health_status == {
        "status": "ok",
        "app": "test-app",
        "environment": "test",
    }