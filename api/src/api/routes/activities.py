# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Shared activity routes for the public API."""

from datetime import datetime, timezone

from fastapi import APIRouter
from learnwithai.tables.activity import Activity
from learnwithai.tables.membership import MembershipType

from ..di import (
    ActivityByPathDI,
    ActivityServiceDI,
    AuthenticatedUserDI,
    CourseByCourseIDPathDI,
    MembershipRepositoryDI,
    SubmissionRepositoryDI,
)
from ..models import (
    ActivityResponse,
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
