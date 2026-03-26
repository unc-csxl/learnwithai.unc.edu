"""RabbitMQ broker configuration for Dramatiq workers."""

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from learnwithai.config import get_settings


def configure_broker() -> RabbitmqBroker:
    """Creates and registers the shared Dramatiq RabbitMQ broker."""
    settings = get_settings()
    broker = RabbitmqBroker(url=settings.effective_rabbitmq_url)
    dramatiq.set_broker(broker)
    return broker
