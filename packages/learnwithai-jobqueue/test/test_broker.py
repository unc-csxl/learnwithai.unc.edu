from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import Mock, patch

import learnwithai_jobqueue
from learnwithai_jobqueue import broker


def test_configure_broker_builds_and_registers_rabbitmq_broker() -> None:
    # Arrange
    settings = SimpleNamespace(effective_rabbitmq_url="amqp://guest:guest@test/")
    expected_broker = object()

    # Act
    with patch("learnwithai_jobqueue.broker.get_settings", return_value=settings), patch(
        "learnwithai_jobqueue.broker.RabbitmqBroker", return_value=expected_broker
    ) as rabbitmq_broker_mock, patch("learnwithai_jobqueue.broker.dramatiq.set_broker") as set_broker_mock:
        configured_broker = broker.configure_broker()

    # Assert
    assert configured_broker is expected_broker
    rabbitmq_broker_mock.assert_called_once_with(url="amqp://guest:guest@test/")
    set_broker_mock.assert_called_once_with(expected_broker)


def test_package_initialization_exports_and_runs_configure_broker() -> None:
    # Arrange
    configure_broker_mock = Mock()

    # Act
    with patch.object(broker, "configure_broker", configure_broker_mock):
        reloaded_package = importlib.reload(learnwithai_jobqueue)

    # Assert
    assert reloaded_package.__all__ == ["configure_broker"]
    configure_broker_mock.assert_called_once_with()