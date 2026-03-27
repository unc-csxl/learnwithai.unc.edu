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


def flush_broker_queues() -> None:
    """Purges all declared Dramatiq queues.

    This is used by development reset flows so stale delayed or retried jobs
    cannot outlive a database reset and interfere with later test runs.
    """
    configure_broker().flush_all()
