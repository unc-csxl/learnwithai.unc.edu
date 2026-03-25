"""Operational health routes for the API."""

from fastapi import APIRouter

from learnwithai.services.health import get_health_status
from learnwithai.jobs import EchoJob

from ..di import JobQueueDI

router = APIRouter(tags=["Operations"])


@router.get(
    "/health",
    summary="Get service health",
    response_description="Current health details for the API service.",
)
def health() -> dict[str, str]:
    """Returns the current service health payload."""
    return get_health_status()


@router.post(
    "/queue",
    summary="Enqueue a sample background job",
    response_description="Acknowledgement that the demo job was submitted.",
)
def queue(job_queue: JobQueueDI) -> str:
    """Enqueues a sample background job.

    Args:
        job_queue: Queue implementation used to submit background work.

    Returns:
        A simple acknowledgement when the job has been enqueued.
    """
    job_queue.enqueue(EchoJob(message="hello"))
    return "ok"
