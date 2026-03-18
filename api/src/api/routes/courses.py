"""Course management routes for the public API."""

from fastapi import APIRouter

from ..dependency_injection import (
    CourseByCourseIDPathDI,
    CourseServiceDI,
    CurrentUserDI,
    SessionDI,
    UserByAddMemberRequestPIDDI,
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
        404: {"description": "Course not found."},
    },
)
def get_course_roster(
    course: CourseByCourseIDPathDI,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> list[MembershipResponse]:
    """Returns the full roster for a course.

    Only instructors and TAs may view the roster.

    Args:
        course: Course loaded via DI and course_id Path param.
        user: Authenticated user.
        course_svc: Service used to query the roster.

    Returns:
        List of memberships for the course.
    """
    memberships = course_svc.get_course_roster(course, user)
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
    body: AddMemberRequest,
    session: SessionDI,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
    target_user: UserByAddMemberRequestPIDDI,
) -> MembershipResponse:
    """Adds a member to a course.

    Only the instructor of the course may add members.

    Args:
        course: Course loaded via DI and course_id path param.
        body: Member addition payload.
        session: Database session scoped to the request.
        user: Authenticated user.
        course_svc: Service used to manage memberships.
        target_user: User loaded from the request payload pid.

    Returns:
        The newly created membership.
    """
    with session.begin():
        membership = course_svc.add_member(
            course,
            user,
            target_user,
            body.type,
        )
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
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
) -> MembershipResponse:
    """Drops a member from a course.

    Instructors can drop anyone. Students and TAs can drop themselves.

    Args:
        course: Course loaded via DI and course_id path param.
        target_user: User loaded via DI and pid path param.
        session: Database session scoped to the request.
        user: Authenticated user.
        course_svc: Service used to manage memberships.

    Returns:
        The updated membership.
    """
    with session.begin():
        membership = course_svc.drop_member(user, course, target_user)
    return MembershipResponse.model_validate(membership)
