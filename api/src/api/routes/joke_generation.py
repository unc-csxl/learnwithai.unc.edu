"""Joke generation routes for the public API."""

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException

from ..di import (
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    CourseServiceDI,
    JokeGenerationServiceDI,
)
from ..models import CreateJokeRequest, JokeRequestResponse

router = APIRouter(prefix="/courses/{course_id}/joke-requests", tags=["Instructor Tools"])


def _build_response(job: object) -> JokeRequestResponse:
    """Builds a JokeRequestResponse from an AsyncJob record.

    Args:
        job: An AsyncJob instance loaded from the database.

    Returns:
        A serializable response model.
    """
    input_data: dict = getattr(job, "input_data", None) or {}  # type: ignore[assignment]
    output_data: dict = getattr(job, "output_data", None) or {}  # type: ignore[assignment]
    return JokeRequestResponse(
        id=job.id,  # type: ignore[arg-type]
        status=job.status,  # type: ignore[arg-type]
        prompt=input_data.get("prompt", ""),
        jokes=output_data.get("jokes", []),
        created_at=job.created_at,  # type: ignore[arg-type]
        completed_at=job.completed_at,  # type: ignore[arg-type]
    )


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
) -> JokeRequestResponse:
    """Submits a joke generation request for a course.

    Only instructors may submit joke requests.

    Args:
        subject: Authenticated subject.
        course: Course loaded via DI from the path.
        body: Request containing the prompt.
        course_svc: Service used for authorization check.
        joke_svc: Joke generation service to create the job.

    Returns:
        The accepted joke generation job.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    job = joke_svc.create_request(subject, course.id, body.prompt)
    return _build_response(job)


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
) -> list[JokeRequestResponse]:
    """Returns all joke generation jobs for a course.

    Only instructors may list joke requests.

    Args:
        subject: Authenticated subject.
        course: Course loaded via DI from the path.
        course_svc: Service used for authorization check.
        joke_svc: Joke generation service to query jobs.

    Returns:
        List of joke generation jobs.
    """
    course_svc.authorize_instructor(subject, course)
    assert course.id is not None
    jobs = joke_svc.list_requests(course.id)
    return [_build_response(j) for j in jobs]


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
    job_id: int,
) -> JokeRequestResponse:
    """Returns a single joke generation job.

    Only instructors may view joke requests.

    Args:
        subject: Authenticated subject.
        course: Course loaded via DI from the path.
        course_svc: Service used for authorization check.
        joke_svc: Joke generation service to load the job.
        job_id: Primary key of the joke generation job.

    Returns:
        The matching joke generation job.
    """
    course_svc.authorize_instructor(subject, course)
    job = joke_svc.get_request(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if job.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    return _build_response(job)


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

    Args:
        subject: Authenticated subject.
        course: Course loaded via DI from the path.
        course_svc: Service used for authorization check.
        joke_svc: Joke generation service to delete the job.
        job_id: Primary key of the joke generation job.
    """
    course_svc.authorize_instructor(subject, course)
    job = joke_svc.get_request(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    assert course.id is not None
    if job.course_id != course.id:
        raise HTTPException(status_code=404, detail="Joke request not found.")
    joke_svc.delete_request(job_id)
