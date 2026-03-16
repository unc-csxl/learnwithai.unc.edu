from fastapi import APIRouter

from learnwithai.services.health import get_health_status
from learnwithai.jobs import EchoJob

from ..dependency_injection import JobQueueDI

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return get_health_status()


@router.post("/queue")
def queue(job_queue: JobQueueDI) -> str:
    job_queue.enqueue(EchoJob(message="hello"))
    return "ok"
