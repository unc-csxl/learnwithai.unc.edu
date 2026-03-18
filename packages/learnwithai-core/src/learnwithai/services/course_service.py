"""Business logic for course and membership management."""

from ..repositories.course_repository import CourseRepository
from ..repositories.membership_repository import MembershipRepository
from ..tables.course import Course
from ..tables.membership import Membership, MembershipState, MembershipType
from ..tables.user import User


class AuthorizationError(Exception):
    """Raised when a user lacks permission for the requested operation."""


class CourseService:
    """Orchestrates course operations with access control enforcement."""

    def __init__(
        self,
        course_repo: CourseRepository,
        membership_repo: MembershipRepository,
    ):
        """Initializes the course service.

        Args:
            course_repo: Repository for course persistence.
            membership_repo: Repository for membership persistence.
        """
        self._course_repo = course_repo
        self._membership_repo = membership_repo

    def create_course(self, user: User, name: str, term: str, section: str) -> Course:
        """Creates a course and enrolls the creator as instructor.

        Args:
            user: Authenticated user creating the course.
            name: Course name.
            term: Academic term (e.g. "Fall 2026").
            section: Section identifier (e.g. "001").

        Returns:
            The newly created course.
        """
        course = self._course_repo.create(Course(name=name, term=term, section=section))
        self._membership_repo.create(
            Membership(
                user_pid=user.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.INSTRUCTOR,
                state=MembershipState.ENROLLED,
            )
        )
        return course

    def get_my_courses(self, user: User) -> list[Course]:
        """Returns courses where the user has an active membership.

        Args:
            user: Authenticated user.

        Returns:
            List of courses where the user is enrolled.
        """
        memberships = self._membership_repo.get_active_by_user(user.pid)
        courses: list[Course] = []
        for m in memberships:
            course = self._course_repo.get_by_id(m.course_id)
            if course is not None:
                courses.append(course)
        return courses

    def get_course_roster(self, user: User, course_id: int) -> list[Membership]:
        """Returns the full roster for a course.

        Only instructors and TAs may view the roster.

        Args:
            user: Authenticated user requesting the roster.
            course_id: Course to query.

        Returns:
            List of all memberships for the course.

        Raises:
            AuthorizationError: If the user is not an instructor or TA.
        """
        self._require_membership(
            user.pid,
            course_id,
            {MembershipType.INSTRUCTOR, MembershipType.TA},
        )
        return self._membership_repo.get_all_by_course(course_id)

    def add_member(
        self,
        user: User,
        course_id: int,
        target_pid: int,
        membership_type: MembershipType,
    ) -> Membership:
        """Adds a member to a course.

        Only an instructor of the course may add members.

        Args:
            user: Authenticated user performing the action.
            course_id: Course to add the member to.
            target_pid: PID of the user to enroll.
            membership_type: Role to assign.

        Returns:
            The newly created membership.

        Raises:
            AuthorizationError: If the requesting user is not an instructor.
        """
        self._require_membership(user.pid, course_id, {MembershipType.INSTRUCTOR})
        return self._membership_repo.create(
            Membership(
                user_pid=target_pid,
                course_id=course_id,
                type=membership_type,
                state=MembershipState.PENDING,
            )
        )

    def drop_member(self, user: User, course_id: int, target_pid: int) -> Membership:
        """Drops a member from a course.

        Instructors can drop anyone. Students and TAs can drop themselves.

        Args:
            user: Authenticated user performing the action.
            course_id: Course to drop the member from.
            target_pid: PID of the user to drop.

        Returns:
            The updated membership with dropped state.

        Raises:
            AuthorizationError: If the user lacks permission.
            ValueError: If the target membership does not exist.
        """
        caller = self._membership_repo.get_by_user_and_course(user.pid, course_id)
        if caller is None or caller.state == MembershipState.DROPPED:
            raise AuthorizationError("Not a member of this course")

        is_self = user.pid == target_pid
        if not is_self and caller.type != MembershipType.INSTRUCTOR:
            raise AuthorizationError("Only instructors can drop other members")

        target = self._membership_repo.get_by_user_and_course(target_pid, course_id)
        if target is None:
            raise ValueError("Target membership does not exist")
        target.state = MembershipState.DROPPED
        return self._membership_repo.update(target)

    def _require_membership(
        self,
        user_pid: int,
        course_id: int,
        allowed_types: set[MembershipType],
    ) -> Membership:
        """Verifies the user holds an active membership with an allowed role.

        Args:
            user_pid: PID to check.
            course_id: Course to check.
            allowed_types: Set of roles that satisfy the requirement.

        Returns:
            The verified membership.

        Raises:
            AuthorizationError: If the check fails.
        """
        membership = self._membership_repo.get_by_user_and_course(user_pid, course_id)
        if membership is None or membership.state == MembershipState.DROPPED:
            raise AuthorizationError("Not a member of this course")
        if membership.type not in allowed_types:
            raise AuthorizationError("Insufficient permissions")
        return membership
