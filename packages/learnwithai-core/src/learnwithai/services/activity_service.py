# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Business logic for activity management with access control."""

from datetime import datetime

from ..errors import AuthorizationError
from ..repositories.activity_repository import ActivityRepository
from ..repositories.membership_repository import MembershipRepository
from ..tables.activity import Activity, ActivityType
from ..tables.course import Course
from ..tables.membership import MembershipType
from ..tables.user import User


class ActivityService:
    """Orchestrates shared activity CRUD with course-level authorization."""

    def __init__(
        self,
        activity_repo: ActivityRepository,
        membership_repo: MembershipRepository,
    ):
        """Initializes the service with its dependencies.

        Args:
            activity_repo: Repository for activity persistence.
            membership_repo: Repository for membership lookups.
        """
        self._activity_repo = activity_repo
        self._membership_repo = membership_repo

    def create_activity(
        self,
        subject: User,
        course: Course,
        activity_type: ActivityType,
        title: str,
        release_date: datetime,
        due_date: datetime,
        late_date: datetime | None = None,
    ) -> Activity:
        """Creates a new activity in a course.

        Only instructors and TAs may create activities.

        Args:
            subject: Authenticated user performing the action.
            course: Course the activity belongs to.
            activity_type: Discriminator for the activity kind.
            title: Display title for the activity.
            release_date: When the activity becomes visible to students.
            due_date: Submission deadline.
            late_date: Optional late submission cutoff.

        Returns:
            The newly created activity.

        Raises:
            AuthorizationError: If the subject is not an instructor or TA.
        """
        self._authorize_staff(subject, course)
        assert course.id is not None
        return self._activity_repo.create(
            Activity(
                course_id=course.id,
                created_by_pid=subject.pid,
                type=activity_type,
                title=title,
                release_date=release_date,
                due_date=due_date,
                late_date=late_date,
            )
        )

    def list_activities(
        self,
        subject: User,
        course: Course,
        now: datetime,
    ) -> list[Activity]:
        """Returns activities visible to the subject.

        Instructors and TAs see all activities. Students see only those
        whose release date has passed.

        Args:
            subject: Authenticated user requesting the list.
            course: Course to list activities for.
            now: Current timestamp for release-date filtering.

        Returns:
            A list of activities the subject is allowed to see.

        Raises:
            AuthorizationError: If the subject is not a course member.
        """
        assert course.id is not None
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")
        if membership.type in {MembershipType.INSTRUCTOR, MembershipType.TA}:
            return self._activity_repo.list_by_course(course.id)
        return self._activity_repo.list_released_by_course(course.id, now)

    def get_activity(
        self,
        subject: User,
        course: Course,
        activity_id: int,
        now: datetime,
    ) -> Activity:
        """Returns a single activity with authorization checks.

        Students may only access released activities.

        Args:
            subject: Authenticated user requesting the activity.
            course: Course the activity belongs to.
            activity_id: Primary key of the activity.
            now: Current timestamp for release-date filtering.

        Returns:
            The activity.

        Raises:
            AuthorizationError: If the subject lacks access.
            ValueError: If the activity does not exist or does not belong
                to the course.
        """
        assert course.id is not None
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")

        activity = self._activity_repo.get_by_id(activity_id)
        if activity is None or activity.course_id != course.id:
            raise ValueError(f"Activity {activity_id} not found in course")

        if membership.type == MembershipType.STUDENT:
            if activity.release_date > now:
                raise AuthorizationError("Activity is not yet released")

        return activity

    def update_activity(
        self,
        subject: User,
        course: Course,
        activity: Activity,
        title: str,
        release_date: datetime,
        due_date: datetime,
        late_date: datetime | None = None,
    ) -> Activity:
        """Updates an activity's shared metadata.

        Only instructors and TAs may update activities.

        Args:
            subject: Authenticated user performing the action.
            course: Course the activity belongs to.
            activity: The activity to update.
            title: Updated title.
            release_date: Updated release date.
            due_date: Updated due date.
            late_date: Updated late submission cutoff.

        Returns:
            The updated activity.

        Raises:
            AuthorizationError: If the subject is not an instructor or TA.
        """
        self._authorize_staff(subject, course)
        activity.title = title
        activity.release_date = release_date
        activity.due_date = due_date
        activity.late_date = late_date
        return self._activity_repo.update(activity)

    def delete_activity(
        self,
        subject: User,
        course: Course,
        activity: Activity,
    ) -> None:
        """Deletes an activity.

        Only instructors may delete activities.

        Args:
            subject: Authenticated user performing the action.
            course: Course the activity belongs to.
            activity: The activity to delete.

        Raises:
            AuthorizationError: If the subject is not an instructor.
        """
        membership = self._membership_repo.get_by_user_and_course(subject, course)
        if membership is None:
            raise AuthorizationError("Not a member of this course")
        if membership.type != MembershipType.INSTRUCTOR:
            raise AuthorizationError("Only instructors can delete activities")
        self._activity_repo.delete(activity)

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
