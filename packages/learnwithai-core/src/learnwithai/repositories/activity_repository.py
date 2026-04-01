"""Persistence helpers for activity records."""

from datetime import datetime

from sqlmodel import col, select

from ..db import Session
from ..tables.activity import Activity


class ActivityRepository:
    """Provides activity lookup and persistence operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write activity records.
        """
        self._session = session

    def create(self, activity: Activity) -> Activity:
        """Persists a new activity and reloads database defaults.

        Args:
            activity: Activity instance to insert.

        Returns:
            The persisted activity with refreshed database state.
        """
        self._session.add(activity)
        self._session.flush()
        self._session.refresh(activity)
        return activity

    def get_by_id(self, activity_id: int) -> Activity | None:
        """Looks up an activity by primary key.

        Args:
            activity_id: Activity identifier.

        Returns:
            The matching activity when found; otherwise, ``None``.
        """
        return self._session.get(Activity, activity_id)

    def list_by_course(self, course_id: int) -> list[Activity]:
        """Returns all activities for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of activities ordered by creation time descending.
        """
        stmt = (
            select(Activity)
            .where(Activity.course_id == course_id)
            .order_by(col(Activity.created_at).desc())
        )
        return list(self._session.exec(stmt).all())

    def list_released_by_course(
        self, course_id: int, now: datetime
    ) -> list[Activity]:
        """Returns released activities for a course, newest first.

        An activity is considered released when its ``release_date`` is
        at or before *now*.

        Args:
            course_id: The course to filter by.
            now: Current timestamp used for the release check.

        Returns:
            A list of released activities ordered by creation time descending.
        """
        stmt = (
            select(Activity)
            .where(
                Activity.course_id == course_id,
                col(Activity.release_date) <= now,
            )
            .order_by(col(Activity.created_at).desc())
        )
        return list(self._session.exec(stmt).all())

    def update(self, activity: Activity) -> Activity:
        """Merges changes to an existing activity and refreshes state.

        Args:
            activity: Activity instance with updated fields.

        Returns:
            The updated activity with refreshed database state.
        """
        self._session.add(activity)
        self._session.flush()
        self._session.refresh(activity)
        return activity

    def delete(self, activity: Activity) -> None:
        """Deletes an activity.

        Args:
            activity: Activity instance to remove.
        """
        self._session.delete(activity)
        self._session.flush()
