"""Persistence helpers for course records."""

from ..db import Session
from ..tables.course import Course


class CourseRepository:
    """Provides course lookup and persistence operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write course records.
        """
        self._session = session

    def create(self, course: Course) -> Course:
        """Persists a new course and reloads database defaults.

        Args:
            course: Course instance to insert.

        Returns:
            The persisted course with refreshed database state.
        """
        self._session.add(course)
        self._session.flush()
        self._session.refresh(course)
        return course

    def get_by_id(self, course_id: int) -> Course | None:
        """Looks up a course by primary key.

        Args:
            course_id: Course identifier.

        Returns:
            The matching course when found; otherwise, ``None``.
        """
        return self._session.get(Course, course_id)

    def update(self, course: Course) -> Course:
        """Merges changes to an existing course and refreshes state.

        Args:
            course: Course instance with updated fields.

        Returns:
            The updated course with refreshed database state.
        """
        merged = self._session.merge(course)
        self._session.flush()
        self._session.refresh(merged)
        return merged

    def delete(self, course: Course) -> None:
        """Deletes a course.

        Args:
            course: Course instance to remove.
        """
        self._session.delete(course)
        self._session.flush()
