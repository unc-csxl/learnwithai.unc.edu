"""Real-time job update delivery pipeline.

Bridges background job status changes from RabbitMQ to connected
WebSocket clients.

Data flow::

    Dramatiq worker
      → RabbitMQJobNotifier (sync pika publish)
        → RabbitMQ ``job_updates`` fanout exchange
          → consumer.py (async aio-pika subscribe)
            → manager.py (per-user WebSocket fan-out)

Modules:
    consumer
        Async background task that subscribes to the fanout exchange
        and forwards messages to the manager.
    manager
        In-memory subscription registry mapping ``(user_id, course_id)``
        to connected WebSocket clients.
"""

from .consumer import consume_job_updates, handle_job_update_message
from .manager import JobUpdateManager

__all__ = [
    "JobUpdateManager",
    "consume_job_updates",
    "handle_job_update_message",
]
