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

    def create_course(
        self, subject: User, name: str, term: str, section: str
    ) -> Course:
        """Creates a course and enrolls the creator as instructor.

        Args:
            subject: Authenticated subject creating the course.
            name: Course name.
            term: Academic term (e.g. "Fall 2026").
            section: Section identifier (e.g. "001").

        Returns:
            The newly created course.
        """
        course = self._course_repo.create(Course(name=name, term=term, section=section))
        self._membership_repo.create(
            Membership(
                user_pid=subject.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.INSTRUCTOR,
                state=MembershipState.ENROLLED,
            )
        )
        return course

    def get_my_courses(self, subject: User) -> list[Course]:
        """Returns courses where the subject has an active membership.

        Args:
            subject: Authenticated subject.

        Returns:
            List of courses where the subject is enrolled.
        """
        memberships = self._membership_repo.get_active_by_user(subject)
        courses: list[Course] = []
        for m in memberships:
            course = self._course_repo.get_by_id(m.course_id)
            if course is not None:
                courses.append(course)
        return courses

    def get_course_roster(
        self,
        subject: User,
        course: Course,
    ) -> list[Membership]:
        """Returns the full roster for a course.

        Only instructors and TAs may view the roster.

        Args:
            subject: Authenticated subject requesting the roster.
            course: Course whose roster should be returned.

        Returns:
            List of all memberships for the course.

        Raises:
            AuthorizationError: If the user is not an instructor or TA.
        """
        requester_membership = self._membership_repo.get_by_user_and_course(
            subject, course
        )
        self._require_membership(
            requester_membership,
            {MembershipType.INSTRUCTOR, MembershipType.TA},
        )
        return self._membership_repo.get_all_by_course(course)

    def add_member(
        self,
        subject: User,
        course: Course,
        target_user: User,
        membership_type: MembershipType,
    ) -> Membership:
        """Adds a member to a course.

        Only an instructor of the course may add members.

        Args:
            subject: Authenticated subject performing the action.
            course: Course to add the member to.
            target_user: User to enroll.
            membership_type: Role to assign.

        Returns:
            The newly created membership.

        Raises:
            AuthorizationError: If the requesting user is not an instructor.
        """
        requester_membership = self._membership_repo.get_by_user_and_course(
            subject, course
        )
        self._require_membership(requester_membership, {MembershipType.INSTRUCTOR})
        course_id = course.id
        if course_id is None:
            raise ValueError("Course must be persisted before adding members")

        return self._membership_repo.create(
            Membership(
                user_pid=target_user.pid,
                course_id=course_id,
                type=membership_type,
                state=MembershipState.PENDING,
            )
        )

    def drop_member(
        self,
        subject: User,
        course: Course,
        target_user: User,
    ) -> Membership:
        """Drops a member from a course.

        Instructors can drop anyone. Students and TAs can drop themselves.

        Args:
            subject: Authenticated subject performing the action.
            course: Course from which the user should be dropped.
            target_user: User whose membership should be dropped.

        Returns:
            The updated membership with dropped state.

        Raises:
            AuthorizationError: If the user lacks permission.
            ValueError: If the target membership does not exist.
        """
        requester_membership = self._membership_repo.get_by_user_and_course(
            subject, course
        )
        caller = self._require_membership(
            requester_membership,
            {
                MembershipType.INSTRUCTOR,
                MembershipType.TA,
                MembershipType.STUDENT,
            },
        )
        target_membership = self._membership_repo.get_by_user_and_course(
            target_user, course
        )

        if target_membership is None:
            course_id = course.id if course.id is not None else "unknown"
            raise ValueError(f"Target membership does not exist for course {course_id}")

        is_self = subject.pid == target_membership.user_pid
        if not is_self and caller.type != MembershipType.INSTRUCTOR:
            raise AuthorizationError("Only instructors can drop other members")

        target_membership.state = MembershipState.DROPPED
        return self._membership_repo.update(target_membership)

    def _require_membership(
        self,
        membership: Membership | None,
        allowed_types: set[MembershipType],
    ) -> Membership:
        """Verifies the user holds an active membership with an allowed role.

        Args:
            membership: Membership to validate.
            allowed_types: Set of roles that satisfy the requirement.

        Returns:
            The verified membership.

        Raises:
            AuthorizationError: If the check fails.
        """
        if membership is None or membership.state == MembershipState.DROPPED:
            raise AuthorizationError("Not a member of this course")
        if membership.type not in allowed_types:
            raise AuthorizationError("Insufficient permissions")
        return membership
