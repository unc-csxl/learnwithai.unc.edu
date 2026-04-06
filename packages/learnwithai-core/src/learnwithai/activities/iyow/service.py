"""Business logic for creating and retrieving IYOW activities."""

from datetime import datetime

from ...errors import AuthorizationError
from ...repositories.activity_repository import ActivityRepository
from ...repositories.membership_repository import MembershipRepository
from ...tables.activity import Activity, ActivityType
from ...tables.course import Course
from ...tables.membership import MembershipType
from ...tables.user import User
from .repository import IyowActivityRepository
from .tables import IyowActivity


class IyowActivityService:
    """Orchestrates creation and retrieval of In Your Own Words activities."""

    def __init__(
        self,
        activity_repo: ActivityRepository,
        iyow_activity_repo: IyowActivityRepository,
        membership_repo: MembershipRepository,
    ):
        """Initializes the service with its dependencies.

        Args:
            activity_repo: Repository for base activity records.
            iyow_activity_repo: Repository for IYOW-specific detail records.
            membership_repo: Repository for course membership lookups.
        """
        self._activity_repo = activity_repo
        self._iyow_activity_repo = iyow_activity_repo
        self._membership_repo = membership_repo

    def create_iyow_activity(
        self,
        subject: User,
        course: Course,
        title: str,
        prompt: str,
        rubric: str,
        release_date: datetime,
        due_date: datetime,
        late_date: datetime | None = None,
    ) -> tuple[Activity, IyowActivity]:
        """Creates a base activity and its IYOW detail in one operation.

        Only instructors and TAs may create activities.

        Args:
            subject: Authenticated user performing the action.
            course: Course the activity belongs to.
            title: Display title for the activity.
            prompt: The question or prompt shown to students.
            rubric: Hidden rubric guiding LLM feedback.
            release_date: When the activity becomes visible to students.
            due_date: Submission deadline.
            late_date: Optional late submission cutoff.

        Returns:
            A tuple of the base activity and its IYOW detail.

        Raises:
            AuthorizationError: If the subject is not an instructor or TA.
        """
        self._authorize_staff(subject, course)
        assert course.id is not None

        activity = self._activity_repo.create(
            Activity(
                course_id=course.id,
                created_by_pid=subject.pid,
                type=ActivityType.IYOW,
                title=title,
                release_date=release_date,
                due_date=due_date,
                late_date=late_date,
            )
        )
        assert activity.id is not None

        iyow_detail = self._iyow_activity_repo.create(
            IyowActivity(
                activity_id=activity.id,
                prompt=prompt,
                rubric=rubric,
            )
        )
        return activity, iyow_detail

    def get_iyow_detail(self, activity_id: int) -> IyowActivity:
        """Returns the IYOW-specific detail for an activity.

        Args:
            activity_id: Primary key of the base activity.

        Returns:
            The IYOW detail record.

        Raises:
            ValueError: If no IYOW detail exists for the activity.
        """
        detail = self._iyow_activity_repo.get_by_activity_id(activity_id)
        if detail is None:
            raise ValueError(f"IYOW detail not found for activity {activity_id}")
        return detail

    def update_iyow_activity(
        self,
        subject: User,
        course: Course,
        activity: Activity,
        title: str,
        prompt: str,
        rubric: str,
        release_date: datetime,
        due_date: datetime,
        late_date: datetime | None = None,
    ) -> tuple[Activity, IyowActivity]:
        """Updates both base activity metadata and IYOW-specific detail.

        Only instructors and TAs may update activities.

        Args:
            subject: Authenticated user performing the action.
            course: Course the activity belongs to.
            activity: The base activity to update.
            title: Updated title.
            prompt: Updated prompt text.
            rubric: Updated rubric text.
            release_date: Updated release date.
            due_date: Updated due date.
            late_date: Updated late submission cutoff.

        Returns:
            A tuple of the updated base activity and IYOW detail.

        Raises:
            AuthorizationError: If the subject is not an instructor or TA.
            ValueError: If the IYOW detail does not exist.
        """
        self._authorize_staff(subject, course)

        activity.title = title
        activity.release_date = release_date
        activity.due_date = due_date
        activity.late_date = late_date
        updated_activity = self._activity_repo.update(activity)

        detail = self.get_iyow_detail(activity.id)  # type: ignore[arg-type]
        detail.prompt = prompt
        detail.rubric = rubric
        updated_detail = self._iyow_activity_repo.update(detail)

        return updated_activity, updated_detail

    def _authorize_staff(self, subject: User, course: Course) -> None:
        """Verifies the subject is an instructor or TA of the course.

        Args:
            subject: User to authorize.
            course: Course to check membership for.

        Raises:
            AuthorizationError: If the subject is not staff.
        """
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")
        if membership.type not in {MembershipType.INSTRUCTOR, MembershipType.TA}:
            raise AuthorizationError("Insufficient permissions")
