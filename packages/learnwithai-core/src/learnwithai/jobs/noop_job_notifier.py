# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""No-op job notifier for use in tests and contexts without RabbitMQ."""

from ..interfaces.jobs import JobNotifier, JobUpdate


class NoOpJobNotifier(JobNotifier):
    """Silently discards all job notifications.

    Used in test suites and job handlers that run inside the same
    process where no external notification is needed.
    """

    def notify(self, update: JobUpdate) -> None:
        """Accepts and discards the update."""
        pass
