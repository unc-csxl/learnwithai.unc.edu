"""Course management routes for the public API."""

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException

from ..dependency_injection import (
    CourseByCourseIDPathDI,
    CourseServiceDI,
    AuthenticatedUserDI,
    SessionDI,
    UserRepositoryDI,
    UserByPIDPathDI,
)
from ..models import (
    AddMemberRequest,
    CourseResponse,
    CreateCourseRequest,
    MembershipResponse,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post(
    "",
    response_model=CourseResponse,
    status_code=201,
    summary="Create a course",
    response_description="The newly created course.",
    responses={401: {"description": "Not authenticated."}},
)
def create_course(
    body: Annotated[CreateCourseRequest, Body()],
    session: SessionDI,
    subject: AuthenticatedUserDI,
    course_svc: CourseServiceDI,
) -> CourseResponse:
    """Creates a new course and enrolls the caller as instructor.

    Args:
        body: Course creation payload.
        session: Database session scoped to the request.
        subject: Authenticated subject.
        course_svc: Service used to create the course.

    Returns:
        The newly created course.
    """
    course = course_svc.create_course(subject, body.name, body.term, body.section)
    session.commit()
    return CourseResponse.model_validate(course)


@router.get(
    "",
    response_model=list[CourseResponse],
    summary="List my courses",
    response_description="Courses where the current user has active membership.",
    responses={401: {"description": "Not authenticated."}},
)
def list_my_courses(
    subject: AuthenticatedUserDI,
    course_svc: CourseServiceDI,
) -> list[CourseResponse]:
    """Returns courses the authenticated subject is enrolled in.

    Args:
        subject: Authenticated subject.
        course_svc: Service used to query courses.

    Returns:
        List of courses with active membership.
    """
    courses = course_svc.get_my_courses(subject)
    return [CourseResponse.model_validate(c) for c in courses]


@router.get(
    "/{course_id}/roster",
    response_model=list[MembershipResponse],
    summary="Get course roster",
    response_description="All memberships for the course.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Course not found."},
    },
)
def get_course_roster(
    course: CourseByCourseIDPathDI,
    subject: AuthenticatedUserDI,
    course_svc: CourseServiceDI,
) -> list[MembershipResponse]:
    """Returns the full roster for a course.

    Only instructors and TAs may view the roster.

    Args:
        course: Course loaded via DI and course_id Path param.
        subject: Authenticated subject.
        course_svc: Service used to query the roster.

    Returns:
        List of memberships for the course.
    """
    memberships = course_svc.get_course_roster(course, subject)
    return [MembershipResponse.model_validate(m) for m in memberships]


@router.post(
    "/{course_id}/members",
    response_model=MembershipResponse,
    status_code=201,
    summary="Add a member to a course",
    response_description="The newly created membership.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Only instructors can add members."},
        404: {"description": "Course or user not found."},
    },
)
def add_member(
    course: CourseByCourseIDPathDI,
    add_member_request: Annotated[AddMemberRequest, Body()],
    session: SessionDI,
    subject: AuthenticatedUserDI,
    course_svc: CourseServiceDI,
    user_repo: UserRepositoryDI,
) -> MembershipResponse:
    """Adds a member to a course.

    Only the instructor of the course may add members.

    Args:
        course: Course loaded via DI and course_id path param.
        body: Member addition payload.
        session: Database session scoped to the request.
        subject: Authenticated subject.
        course_svc: Service used to manage memberships.
        user_repo: Repository used to load the target user from the request body.

    Returns:
        The newly created membership.
    """
    target_user = user_repo.get_by_pid(add_member_request.pid)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    membership = course_svc.add_member(
        course,
        subject,
        target_user,
        add_member_request.type,
    )
    session.commit()
    return MembershipResponse.model_validate(membership)


@router.delete(
    "/{course_id}/members/{pid}",
    response_model=MembershipResponse,
    summary="Drop a member from a course",
    response_description="The updated membership with dropped state.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions to drop this member."},
        404: {"description": "Course or user not found."},
    },
)
def drop_member(
    course: CourseByCourseIDPathDI,
    target_user: UserByPIDPathDI,
    session: SessionDI,
    subject: AuthenticatedUserDI,
    course_svc: CourseServiceDI,
) -> MembershipResponse:
    """Drops a member from a course.

    Instructors can drop anyone. Students and TAs can drop themselves.

    Args:
        course: Course loaded via DI and course_id path param.
        target_user: User loaded via DI and pid path param.
        session: Database session scoped to the request.
        subject: Authenticated subject.
        course_svc: Service used to manage memberships.

    Returns:
        The updated membership.
    """
    membership = course_svc.drop_member(subject, course, target_user)
    session.commit()
    return MembershipResponse.model_validate(membership)
