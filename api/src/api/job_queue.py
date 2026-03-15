from typing import TypeAlias, Annotated
from fastapi import Depends

from learnwithai.interfaces import JobQueue
from learnwithai_jobqueue.dramatiq_job_queue import DramatiqJobQueue


def job_queue_factory() -> JobQueue:
    return DramatiqJobQueue()


JobQueueDI: TypeAlias = Annotated[JobQueue, Depends(job_queue_factory)]
