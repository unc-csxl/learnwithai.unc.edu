# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Sample echo job used to validate queue integration."""

from typing import Literal

from ..interfaces import Job, JobHandler
from ..services.health import get_health_status


class EchoJob(Job):
    """Represents a simple echo payload for background execution."""

    type: Literal["echo"] = "echo"
    message: str


class EchoJobHandler(JobHandler[EchoJob]):
    """Processes echo jobs by logging their payload and service health.

    Extends ``JobHandler`` directly instead of ``BaseJobHandler`` because
    echo jobs are stateless diagnostics — no database tracking or session
    lifecycle is needed.
    """

    def handle(self, job: EchoJob) -> None:
        """Handles an echo job.

        Args:
            job: Echo job payload to process.
        """
        status = get_health_status()
        print(
            {
                "task": "echo_job",
                "payload": job,
                "core_status": status,
            }
        )
