"""Joke generation routes for the public API."""

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from learnwithai.tables.async_job import AsyncJobStatus
from learnwithai.tools.jokes.tables import JokeRequest

from ..di import (
    AsyncJobRepositoryDI,
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    CourseServiceDI,
    JokeGenerationServiceDI,
)
from ..models import CreateJokeRequest, JokeRequestResponse

router = APIRouter(prefix="/courses/{course_id}/joke-requests", tags=["Instructor Tools"])


def _build_response(
    joke_request: JokeRequest,
    status: AsyncJobStatus,
    completed_at: object = None,
) -> JokeRequestResponse:
    """Builds a JokeRequestResponse from a JokeRequest and its job status.

    Args:
        joke_request: The joke request record.
        status: Status from the linked AsyncJob.
        completed_at: Completion timestamp from the linked AsyncJob.

    Returns:
        A serializable response model.
    """
    return JokeRequestResponse(
        id=joke_request.id,  # type: ignore[arg-type]
        status=status,
        prompt=joke_request.prompt,
        jokes=joke_request.jokes,
        created_at=joke_request.created_at,  # type: ignore[arg-type]
        completed_at=completed_at,  # type: ignore[arg-type]
    )


def _get_job_status(
    joke_request: JokeRequest,
    async_job_repo: AsyncJobRepositoryDI,
) -> tuple[AsyncJobStatus, object]:
    """Resolves the status and completion time from the linked async job.

    Args:
        joke_request: The joke request with an async_job_id link.
        async_job_repo: Repository to fetch the async job.

    Returns:
        A tuple of (status, completed_at).
    """
    if joke_request.async_job_id is not None:
        async_job = async_job_repo.get_by_id(joke_request.async_job_id)
        if async_job is not None:
            return async_job.status, async_job.completed_at
    return AsyncJobStatus.PENDING, None


@router.post(
    "",
    response_model=JokeRequestResponse,
    status_code=202,
    summary="Submit a joke generation request",
    response_description="The accepted joke generation job.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course not found."},
    },
)
def create_joke_request(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    body: Annotated[CreateJokeRequest, Body()],
    course_svc: CourseServiceDI,
    joke_svc: JokeGenerationServiceDI,
    async_job_repo: AsyncJobRepositoryDI,
) -> JokeRequestResponse:
    """Submits a joke generation request for a course.

    Only instructors may submit joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    joke_request = joke_svc.create_request(subject, course.id, body.prompt)
    status, completed_at = _get_job_status(joke_request, async_job_repo)
    return _build_response(joke_request, status, completed_at)


@router.get(
    "",
    response_model=list[JokeRequestResponse],
    summary="List joke generation requests",
    response_description="All joke generation jobs for the course.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course not found."},
    },
)
def list_joke_requests(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    course_svc: CourseServiceDI,
    joke_svc: JokeGenerationServiceDI,
    async_job_repo: AsyncJobRepositoryDI,
) -> list[JokeRequestResponse]:
    """Returns all joke generation jobs for a course.

    Only instructors may list joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    joke_requests = joke_svc.list_requests(course.id)
    results = []
    for jr in joke_requests:
        status, completed_at = _get_job_status(jr, async_job_repo)
        results.append(_build_response(jr, status, completed_at))
    return results


@router.get(
    "/{job_id}",
    response_model=JokeRequestResponse,
    summary="Get a joke generation request",
    response_description="Details of a single joke generation job.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course or job not found."},
    },
)
def get_joke_request(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    course_svc: CourseServiceDI,
    joke_svc: JokeGenerationServiceDI,
    async_job_repo: AsyncJobRepositoryDI,
    job_id: int,
) -> JokeRequestResponse:
    """Returns a single joke generation job.

    Only instructors may view joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    joke_request = joke_svc.get_request(job_id)
    if joke_request is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if joke_request.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    status, completed_at = _get_job_status(joke_request, async_job_repo)
    return _build_response(joke_request, status, completed_at)


@router.delete(
    "/{job_id}",
    status_code=204,
    summary="Delete a joke generation request",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course or job not found."},
    },
)
def delete_joke_request(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    course_svc: CourseServiceDI,
    joke_svc: JokeGenerationServiceDI,
    job_id: int,
) -> None:
    """Deletes a joke generation job.

    Only instructors may delete joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    joke_request = joke_svc.get_request(job_id)
    if joke_request is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if joke_request.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    joke_svc.delete_request(job_id)
