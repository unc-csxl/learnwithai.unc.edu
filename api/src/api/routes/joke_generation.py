"""Joke generation routes for the public API."""

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from learnwithai.tables.async_job import AsyncJob
from learnwithai.tools.jokes.tables import Joke

from ..di import (
    AsyncJobRepositoryDI,
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    CourseServiceDI,
    JokeGenerationServiceDI,
)
from ..models import AsyncJobInfo, CreateJokeRequest, JokeResponse

router = APIRouter(prefix="/courses/{course_id}/joke-requests", tags=["Instructor Tools"])


def _build_job_info(async_job: AsyncJob | None) -> AsyncJobInfo | None:
    """Builds an AsyncJobInfo from an AsyncJob, if present.

    Args:
        async_job: The linked async job, or ``None``.

    Returns:
        A nested job info model, or ``None`` when no job exists.
    """
    if async_job is None:
        return None
    return AsyncJobInfo(
        id=async_job.id,  # type: ignore[arg-type]
        status=async_job.status,
        completed_at=async_job.completed_at,
    )


def _build_response(
    joke: Joke,
    async_job: AsyncJob | None,
) -> JokeResponse:
    """Builds a JokeResponse from a Joke and its optional linked job.

    Args:
        joke: The joke record.
        async_job: The linked async job, or ``None``.

    Returns:
        A serializable response model.
    """
    return JokeResponse(
        id=joke.id,  # type: ignore[arg-type]
        prompt=joke.prompt,
        jokes=joke.jokes,
        created_at=joke.created_at,  # type: ignore[arg-type]
        job=_build_job_info(async_job),
    )


def _get_async_job(
    joke: Joke,
    async_job_repo: AsyncJobRepositoryDI,
) -> AsyncJob | None:
    """Resolves the linked async job for a single joke.

    Args:
        joke: The joke with an async_job_id link.
        async_job_repo: Repository to fetch the async job.

    Returns:
        The linked async job, or ``None`` when not found.
    """
    if joke.async_job_id is not None:
        return async_job_repo.get_by_id(joke.async_job_id)
    return None


@router.post(
    "",
    response_model=JokeResponse,
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
) -> JokeResponse:
    """Submits a joke generation request for a course.

    Only instructors may submit joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    joke = joke_svc.create_request(subject, course.id, body.prompt)
    async_job = _get_async_job(joke, async_job_repo)
    return _build_response(joke, async_job)


@router.get(
    "",
    response_model=list[JokeResponse],
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
) -> list[JokeResponse]:
    """Returns all joke generation jobs for a course.

    Only instructors may list joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    rows = joke_svc.list_requests_with_jobs(course.id)
    return [_build_response(joke, async_job) for joke, async_job in rows]


@router.get(
    "/{job_id}",
    response_model=JokeResponse,
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
) -> JokeResponse:
    """Returns a single joke generation job.

    Only instructors may view joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    joke = joke_svc.get_request(job_id)
    if joke is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if joke.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    async_job = _get_async_job(joke, async_job_repo)
    return _build_response(joke, async_job)


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
    joke = joke_svc.get_request(job_id)
    if joke is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if joke.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    joke_svc.delete_request(job_id)
