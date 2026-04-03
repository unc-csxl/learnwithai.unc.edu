"""Persistence helpers for activity records."""

from datetime import datetime

from sqlmodel import col, select

from ..tables.activity import Activity
from .base_repository import BaseRepository


class ActivityRepository(BaseRepository[Activity, int]):
    """Provides activity lookup and persistence operations."""

    @property
    def model_type(self) -> type[Activity]:
        """Returns the SQLModel class managed by this repository."""
        return Activity

    def list_by_course(self, course_id: int) -> list[Activity]:
        """Returns all activities for a course, newest first.

        Args:
            course_id: The course to filter by.

        Returns:
            A list of activities ordered by creation time descending.
        """
        stmt = select(Activity).where(Activity.course_id == course_id).order_by(col(Activity.created_at).desc())
        return list(self._session.exec(stmt).all())

    def list_released_by_course(self, course_id: int, now: datetime) -> list[Activity]:
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
