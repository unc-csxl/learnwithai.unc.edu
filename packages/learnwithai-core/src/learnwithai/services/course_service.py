"""Business logic for course and membership management."""

from ..errors import AuthorizationError
from ..pagination import PaginatedResult, PaginationParams
from ..repositories.course_repository import CourseRepository
from ..repositories.membership_repository import MembershipRepository
from ..tables.course import Course, Term
from ..tables.membership import Membership, MembershipState, MembershipType
from ..tables.user import User


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
        self,
        subject: User,
        course_number: str,
        name: str,
        term: Term,
        year: int,
        description: str = "",
    ) -> Course:
        """Creates a course and enrolls the creator as instructor.

        Args:
            subject: Authenticated subject creating the course.
            course_number: Short identifier (e.g. "COMP423").
            name: Course name.
            term: Academic term.
            year: Academic year.
            description: Optional course description.

        Returns:
            The newly created course.
        """
        course = self._course_repo.create(
            Course(
                course_number=course_number,
                name=name,
                description=description,
                term=term,
                year=year,
            )
        )
        self._membership_repo.create(
            Membership(
                user_pid=subject.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.INSTRUCTOR,
                state=MembershipState.ENROLLED,
            )
        )
        return course

    def get_my_courses(self, subject: User) -> list[Membership]:
        """Returns courses where the subject has an active membership.

        Args:
            subject: Authenticated subject.

        Returns:
            List of active memberships with related course data loaded.
        """
        return self._membership_repo.get_active_by_user(subject)

    def get_course_roster(
        self,
        subject: User,
        course: Course,
        pagination: PaginationParams | None = None,
        query: str = "",
    ) -> PaginatedResult[Membership]:
        """Returns the paginated roster for a course.

        Only instructors and TAs may view the roster.

        Args:
            subject: Authenticated subject requesting the roster.
            course: Course whose roster should be returned.
            pagination: Page and page-size parameters. Defaults to page 1,
                size 25 when *None*.
            query: Optional search string to filter by name, PID, or email.

        Returns:
            A paginated result of memberships for the course.

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
        if pagination is None:
            pagination = PaginationParams()
        return self._membership_repo.get_roster_page(course, pagination, query)

    def authorize_instructor(self, subject: User, course: Course) -> Membership:
        """Verifies the subject is an active instructor of the course.

        Args:
            subject: Authenticated subject to authorize.
            course: Course the subject must be an instructor of.

        Returns:
            The verified instructor membership.

        Raises:
            AuthorizationError: If the subject is not an active instructor.
        """
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        return self._require_membership(membership, {MembershipType.INSTRUCTOR})

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

        if course.id is None:
            raise ValueError("Course must be persisted before adding members")

        return self._membership_repo.create(
            Membership(
                user_pid=target_user.pid,
                course_id=course.id,
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

    def update_course(
        self,
        subject: User,
        course: Course,
        course_number: str,
        name: str,
        term: Term,
        year: int,
        description: str = "",
    ) -> Course:
        """Updates an existing course's details.

        Only instructors of the course may update it.

        Args:
            subject: Authenticated subject performing the action.
            course: Course to update.
            course_number: Updated short identifier.
            name: Updated course name.
            term: Updated academic term.
            year: Updated academic year.
            description: Updated course description.

        Returns:
            The updated course.

        Raises:
            AuthorizationError: If the subject is not an instructor.
        """
        self.authorize_instructor(subject, course)
        course.course_number = course_number
        course.name = name
        course.term = term
        course.year = year
        course.description = description
        return self._course_repo.update(course)

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
