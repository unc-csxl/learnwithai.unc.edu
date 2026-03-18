"""Course management routes for the public API."""

from fastapi import APIRouter

from ..dependency_injection import CourseServiceDI, CurrentUserDI, SessionDI
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
    body: CreateCourseRequest,
    session: SessionDI,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> CourseResponse:
    """Creates a new course and enrolls the caller as instructor.

    Args:
        body: Course creation payload.
        session: Database session scoped to the request.
        user: Authenticated user.
        course_svc: Service used to create the course.

    Returns:
        The newly created course.
    """
    with session.begin():
        course = course_svc.create_course(user, body.name, body.term, body.section)
    return CourseResponse.model_validate(course)


@router.get(
    "",
    response_model=list[CourseResponse],
    summary="List my courses",
    response_description="Courses where the current user has active membership.",
    responses={401: {"description": "Not authenticated."}},
)
def list_my_courses(
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> list[CourseResponse]:
    """Returns courses the authenticated user is enrolled in.

    Args:
        user: Authenticated user.
        course_svc: Service used to query courses.

    Returns:
        List of courses with active membership.
    """
    courses = course_svc.get_my_courses(user)
    return [CourseResponse.model_validate(c) for c in courses]


@router.get(
    "/{course_id}/roster",
    response_model=list[MembershipResponse],
    summary="Get course roster",
    response_description="All memberships for the course.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions."},
    },
)
def get_course_roster(
    course_id: int,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> list[MembershipResponse]:
    """Returns the full roster for a course.

    Only instructors and TAs may view the roster.

    Args:
        course_id: Course to query.
        user: Authenticated user.
        course_svc: Service used to query the roster.

    Returns:
        List of memberships for the course.
    """
    memberships = course_svc.get_course_roster(user, course_id)
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
    },
)
def add_member(
    course_id: int,
    body: AddMemberRequest,
    session: SessionDI,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> MembershipResponse:
    """Adds a member to a course.

    Only the instructor of the course may add members.

    Args:
        course_id: Course to add the member to.
        body: Member addition payload.
        session: Database session scoped to the request.
        user: Authenticated user.
        course_svc: Service used to manage memberships.

    Returns:
        The newly created membership.
    """
    with session.begin():
        membership = course_svc.add_member(user, course_id, body.pid, body.type)
    return MembershipResponse.model_validate(membership)


@router.delete(
    "/{course_id}/members/{pid}",
    response_model=MembershipResponse,
    summary="Drop a member from a course",
    response_description="The updated membership with dropped state.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Insufficient permissions to drop this member."},
    },
)
def drop_member(
    course_id: int,
    pid: int,
    session: SessionDI,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> MembershipResponse:
    """Drops a member from a course.

    Instructors can drop anyone. Students and TAs can drop themselves.

    Args:
        course_id: Course to drop the member from.
        pid: PID of the member to drop.
        session: Database session scoped to the request.
        user: Authenticated user.
        course_svc: Service used to manage memberships.

    Returns:
        The updated membership.
    """
    with session.begin():
        membership = course_svc.drop_member(user, course_id, pid)
    return MembershipResponse.model_validate(membership)
