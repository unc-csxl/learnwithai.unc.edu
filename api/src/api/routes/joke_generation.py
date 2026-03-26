"""Joke generation routes for the public API."""

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from learnwithai.tools.jokes.tables import Joke

from ..di import (
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    CourseServiceDI,
    JokeGenerationServiceDI,
)
from ..models import AsyncJobInfo, CreateJokeRequest, JokeResponse

router = APIRouter(prefix="/courses/{course_id}/joke-requests", tags=["Instructor Tools"])


def _build_response(joke: Joke) -> JokeResponse:
    """Builds a JokeResponse from a Joke using its ``async_job`` relationship.

    Args:
        joke: The joke record with ``async_job`` pre-loaded or lazily available.

    Returns:
        A serializable response model.
    """
    job_info: AsyncJobInfo | None = None
    if joke.async_job is not None:
        job_info = AsyncJobInfo(
            id=joke.async_job.id,  # type: ignore[arg-type]
            status=joke.async_job.status,
            completed_at=joke.async_job.completed_at,
        )
    return JokeResponse(
        id=joke.id,  # type: ignore[arg-type]
        prompt=joke.prompt,
        jokes=joke.jokes,
        created_at=joke.created_at,  # type: ignore[arg-type]
        job=job_info,
    )


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
) -> JokeResponse:
    """Submits a joke generation request for a course.

    Only instructors may submit joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    joke = joke_svc.create(subject, course.id, body.prompt)
    return _build_response(joke)


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
    jokes = joke_svc.list_for_course_with_jobs(course.id)
    return [_build_response(joke) for joke in jokes]


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
    job_id: int,
) -> JokeResponse:
    """Returns a single joke generation job.

    Only instructors may view joke requests.
    """
    course_svc.authorize_instructor(subject, course)
    joke = joke_svc.get(job_id)
    if joke is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if joke.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    return _build_response(joke)


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
    joke = joke_svc.get(job_id)
    if joke is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if joke.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    joke_svc.delete(job_id)
