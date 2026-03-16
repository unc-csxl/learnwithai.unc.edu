import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from learnwithai.config import get_settings


def configure_broker() -> RabbitmqBroker:
    settings = get_settings()
    broker = RabbitmqBroker(url=settings.effective_rabbitmq_url)
    dramatiq.set_broker(broker)
    return broker
