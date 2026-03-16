from typing import Any

import dramatiq

from learnwithai.interfaces import JobQueue, JobHandler
from learnwithai.jobs import Job, job_handler_map, job_adapter


class DramatiqJobQueue(JobQueue):
    def enqueue(self, job: Job) -> None:
        job_queue.send(job.model_dump())


@dramatiq.actor
def job_queue(payload: dict) -> None:
    job: Job = job_adapter(payload)
    handler_class: type[JobHandler[Any]] = job_handler_map[type(job)]
    handler: JobHandler[Any] = handler_class()
    handler.handle(job)
