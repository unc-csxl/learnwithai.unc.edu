"""Activity routes for the public API."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from learnwithai.tables.activity import Activity
from learnwithai.tables.async_job import AsyncJob
from learnwithai.tables.membership import MembershipType
from learnwithai.tables.submission import Submission

from ..di import (
    ActivityByPathDI,
    ActivityServiceDI,
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    IyowActivityServiceDI,
    IyowSubmissionServiceDI,
    MembershipRepositoryDI,
    SubmissionRepositoryDI,
)
from ..models import (
    ActivityResponse,
    AsyncJobInfo,
    CreateIyowActivityRequest,
    IyowActivityResponse,
    IyowSubmissionResponse,
    SubmitIyowRequest,
    UpdateIyowActivityRequest,
)

router = APIRouter(prefix="/courses/{course_id}/activities", tags=["Activities"])


# ---- Response builders ----


def _build_activity_response(
    activity: Activity,
    active_submission_count: int | None = None,
) -> ActivityResponse:
    return ActivityResponse(
        id=activity.id,  # type: ignore[arg-type]
        course_id=activity.course_id,
        type=activity.type,
        title=activity.title,
        release_date=activity.release_date,
        due_date=activity.due_date,
        late_date=activity.late_date,
        created_at=activity.created_at,
        active_submission_count=active_submission_count,
    )


def _build_iyow_response(
    activity: Activity,
    prompt: str,
    rubric: str | None,
) -> IyowActivityResponse:
    return IyowActivityResponse(
        id=activity.id,  # type: ignore[arg-type]
        course_id=activity.course_id,
        type=activity.type,
        title=activity.title,
        prompt=prompt,
        rubric=rubric,
        release_date=activity.release_date,
        due_date=activity.due_date,
        late_date=activity.late_date,
        created_at=activity.created_at,
    )


def _build_submission_response(
    submission: Submission,
    response_text: str,
    feedback: str | None,
    async_job: AsyncJob | None,
) -> IyowSubmissionResponse:
    job_info: AsyncJobInfo | None = None
    if async_job is not None:
        job_info = AsyncJobInfo(
            id=async_job.id,  # type: ignore[arg-type]
            status=async_job.status,
            completed_at=async_job.completed_at,
        )
    return IyowSubmissionResponse(
        id=submission.id,  # type: ignore[arg-type]
        activity_id=submission.activity_id,
        student_pid=submission.student_pid,
        is_active=submission.is_active,
        submitted_at=submission.submitted_at,
        response_text=response_text,
        feedback=feedback,
        job=job_info,
    )


# ---- Activity CRUD ----


@router.get(
    "",
    response_model=list[ActivityResponse],
    summary="List activities for a course",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course not found."},
    },
)
def list_activities(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity_svc: ActivityServiceDI,
    membership_repo: MembershipRepositoryDI,
    submission_repo: SubmissionRepositoryDI,
) -> list[ActivityResponse]:
    """Returns activities visible to the authenticated user."""
    now = datetime.now(timezone.utc)
    activities = activity_svc.list_activities(subject, course, now)

    membership = membership_repo.get_by_user_and_course(subject, course)
    is_staff = membership is not None and membership.type in {
        MembershipType.INSTRUCTOR,
        MembershipType.TA,
    }

    results: list[ActivityResponse] = []
    for a in activities:
        count = None
        if is_staff:
            assert a.id is not None
            count = submission_repo.count_active_by_activity(a.id)
        results.append(_build_activity_response(a, active_submission_count=count))
    return results


@router.post(
    "/iyow",
    response_model=IyowActivityResponse,
    status_code=201,
    summary="Create an IYOW activity",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course not found."},
    },
)
def create_iyow_activity(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    body: Annotated[CreateIyowActivityRequest, Body()],
    iyow_svc: IyowActivityServiceDI,
) -> IyowActivityResponse:
    """Creates a new In Your Own Words activity."""
    activity, detail = iyow_svc.create_iyow_activity(
        subject,
        course,
        body.title,
        body.prompt,
        body.rubric,
        body.release_date,
        body.due_date,
        body.late_date,
    )
    return _build_iyow_response(activity, detail.prompt, detail.rubric)


@router.get(
    "/{activity_id}",
    response_model=IyowActivityResponse,
    summary="Get activity detail",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
    },
)
def get_activity(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    activity_svc: ActivityServiceDI,
    iyow_svc: IyowActivityServiceDI,
    membership_repo: MembershipRepositoryDI,
) -> IyowActivityResponse:
    """Returns full activity detail including type-specific fields.

    Students do not see the rubric.
    """
    now = datetime.now(timezone.utc)
    activity = activity_svc.get_activity(subject, course, activity.id, now)  # type: ignore[arg-type]
    detail = iyow_svc.get_iyow_detail(activity.id)  # type: ignore[arg-type]

    # Hide rubric from students
    membership = membership_repo.get_by_user_and_course(subject, course)
    rubric: str | None = detail.rubric
    if membership is not None and membership.type == MembershipType.STUDENT:
        rubric = None

    return _build_iyow_response(activity, detail.prompt, rubric)


@router.put(
    "/{activity_id}",
    response_model=IyowActivityResponse,
    summary="Update an IYOW activity",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
    },
)
def update_iyow_activity(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    body: Annotated[UpdateIyowActivityRequest, Body()],
    iyow_svc: IyowActivityServiceDI,
) -> IyowActivityResponse:
    """Updates an In Your Own Words activity."""
    updated_activity, updated_detail = iyow_svc.update_iyow_activity(
        subject,
        course,
        activity,
        body.title,
        body.prompt,
        body.rubric,
        body.release_date,
        body.due_date,
        body.late_date,
    )
    return _build_iyow_response(updated_activity, updated_detail.prompt, updated_detail.rubric)


@router.delete(
    "/{activity_id}",
    status_code=204,
    summary="Delete an activity",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
    },
)
def delete_activity(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    activity_svc: ActivityServiceDI,
) -> None:
    """Deletes an activity. Only instructors may delete."""
    activity_svc.delete_activity(subject, course, activity)


# ---- IYOW Submissions ----


@router.post(
    "/{activity_id}/submissions",
    response_model=IyowSubmissionResponse,
    status_code=202,
    summary="Submit a response to an IYOW activity",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
        422: {"description": "Submission window closed or invalid."},
    },
)
def submit_iyow_response(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    body: Annotated[SubmitIyowRequest, Body()],
    iyow_sub_svc: IyowSubmissionServiceDI,
) -> IyowSubmissionResponse:
    """Submits a student's response for LLM feedback."""
    now = datetime.now(timezone.utc)
    try:
        submission, iyow_detail = iyow_sub_svc.submit(subject, course, activity, body.response_text, now)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _build_submission_response(submission, iyow_detail.response_text, None, iyow_detail.async_job)


@router.get(
    "/{activity_id}/submissions",
    response_model=list[IyowSubmissionResponse],
    summary="List submissions for an activity",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
    },
)
def list_submissions(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    iyow_sub_svc: IyowSubmissionServiceDI,
    membership_repo: MembershipRepositoryDI,
) -> list[IyowSubmissionResponse]:
    """Returns submissions. Staff sees all active; students see own history."""
    membership = membership_repo.get_by_user_and_course(subject, course)
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this course")

    if membership.type in {MembershipType.INSTRUCTOR, MembershipType.TA}:
        pairs = iyow_sub_svc.list_submissions_for_activity(subject, course, activity)
    else:
        pairs = iyow_sub_svc.get_student_submissions(subject, course, activity)

    return [
        _build_submission_response(sub, detail.response_text, detail.feedback, detail.async_job)
        for sub, detail in pairs
    ]


@router.get(
    "/{activity_id}/submissions/active",
    response_model=IyowSubmissionResponse | None,
    summary="Get the student's active submission",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
    },
)
def get_active_submission(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    iyow_sub_svc: IyowSubmissionServiceDI,
) -> IyowSubmissionResponse | None:
    """Returns the student's current active submission, if any."""
    result = iyow_sub_svc.get_active_submission(subject, course, activity)
    if result is None:
        return None
    submission, iyow_detail = result
    return _build_submission_response(
        submission, iyow_detail.response_text, iyow_detail.feedback, iyow_detail.async_job
    )


@router.get(
    "/{activity_id}/submissions/history/{student_pid}",
    response_model=list[IyowSubmissionResponse],
    summary="Get a student's full submission history",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Activity not found."},
    },
)
def get_student_submission_history(
    subject: AuthenticatedUserDI,
    course: CourseByCourseIDPathDI,
    activity: ActivityByPathDI,
    student_pid: int,
    iyow_sub_svc: IyowSubmissionServiceDI,
) -> list[IyowSubmissionResponse]:
    """Returns all submissions (active + inactive) for a student on an activity.

    Only instructors and TAs may access this endpoint.
    """
    pairs = iyow_sub_svc.get_student_submission_history(subject, course, activity, student_pid)
    return [
        _build_submission_response(sub, detail.response_text, detail.feedback, detail.async_job)
        for sub, detail in pairs
    ]
