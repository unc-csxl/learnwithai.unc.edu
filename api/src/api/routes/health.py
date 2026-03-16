"""Operational health routes for the API."""

from fastapi import APIRouter

from learnwithai.services.health import get_health_status
from learnwithai.jobs import EchoJob

from ..dependency_injection import JobQueueDI

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Returns the current service health payload."""
    return get_health_status()


@router.post("/queue")
def queue(job_queue: JobQueueDI) -> str:
    """Enqueues a sample background job.

    Args:
        job_queue: Queue implementation used to submit background work.

    Returns:
        A simple acknowledgement when the job has been enqueued.
    """
    job_queue.enqueue(EchoJob(message="hello"))
    return "ok"
