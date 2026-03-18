"""Course management routes for the public API."""

from fastapi import APIRouter, HTTPException

from ..dependency_injection import (
    CourseRepositoryDI,
    CourseServiceDI,
    CurrentUserDI,
    MembershipRepositoryDI,
    SessionDI,
    UserRepositoryDI,
)
from ..models import (
    AddMemberRequest,
    CourseResponse,
    CreateCourseRequest,
    MembershipResponse,
)
from learnwithai.tables.course import Course
from learnwithai.tables.user import User

router = APIRouter(prefix="/courses", tags=["Courses"])


def _get_course_or_404(course_repo: CourseRepositoryDI, course_id: int) -> Course:
    """Loads a course by id or raises an HTTP 404."""
    course = course_repo.get_by_id(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


def _get_user_or_404(user_repo: UserRepositoryDI, pid: int) -> User:
    """Loads a user by pid or raises an HTTP 404."""
    user = user_repo.get_by_pid(pid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


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
    course_repo: CourseRepositoryDI,
    membership_repo: MembershipRepositoryDI,
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
    course = _get_course_or_404(course_repo, course_id)
    requester_membership = membership_repo.get_by_user_and_course(user, course)
    memberships = course_svc.get_course_roster(course, requester_membership)
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
    course_repo: CourseRepositoryDI,
    membership_repo: MembershipRepositoryDI,
    user_repo: UserRepositoryDI,
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
    course = _get_course_or_404(course_repo, course_id)
    requester_membership = membership_repo.get_by_user_and_course(user, course)
    target_user = _get_user_or_404(user_repo, body.pid)

    with session.begin():
        membership = course_svc.add_member(
            course,
            requester_membership,
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
    },
)
def drop_member(
    course_id: int,
    pid: int,
    session: SessionDI,
    user: CurrentUserDI,
    course_svc: CourseServiceDI,
    course_repo: CourseRepositoryDI,
    membership_repo: MembershipRepositoryDI,
    user_repo: UserRepositoryDI,
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
    course = _get_course_or_404(course_repo, course_id)
    requester_membership = membership_repo.get_by_user_and_course(user, course)
    target_user = _get_user_or_404(user_repo, pid)
    target_membership = membership_repo.get_by_user_and_course(target_user, course)

    with session.begin():
        membership = course_svc.drop_member(
            user,
            course,
            requester_membership,
            target_membership,
        )
    return MembershipResponse.model_validate(membership)
