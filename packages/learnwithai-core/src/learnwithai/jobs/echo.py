from typing import Literal

from ..interfaces import Job, JobHandler
from ..services.health import get_health_status


class EchoJob(Job):
    type: Literal["echo"] = "echo"
    message: str


class EchoJobHandler(JobHandler):
    def handle(self, job: EchoJob) -> None:
        status = get_health_status()
        print(
            {
                "task": "echo_job",
                "payload": job,
                "core_status": status,
            }
        )
