import os

import dramatiq
import dramatiq.broker as _broker_mod
from dramatiq.brokers.rabbitmq import RabbitmqBroker


def get_rabbitmq_url() -> str:
    return os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def configure_broker() -> RabbitmqBroker:
    # Idempotent: return the existing broker if it is already a RabbitmqBroker.
    # Checked via the internal global directly to avoid get_broker()'s
    # auto-initialisation, which would create a broker pointed at 127.0.0.1.
    if isinstance(_broker_mod.global_broker, RabbitmqBroker):
        return _broker_mod.global_broker
    broker = RabbitmqBroker(url=get_rabbitmq_url())
    dramatiq.set_broker(broker)
    return broker
