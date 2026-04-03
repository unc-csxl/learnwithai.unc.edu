"""Persistence helpers for membership (user-course join) records."""

from sqlalchemy import String, func, or_
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from ..pagination import PaginatedResult, PaginationParams
from ..tables.course import Course
from ..tables.membership import Membership, MembershipState
from ..tables.user import User
from .base_repository import BaseRepository


class MembershipRepository(BaseRepository[Membership, tuple[int, int]]):
    """Provides membership lookup and persistence operations."""

    @property
    def model_type(self) -> type[Membership]:
        """Returns the SQLModel class managed by this repository."""
        return Membership

    def get_by_user_and_course(self, user: User, course: Course) -> Membership | None:
        """Looks up a membership by user and course.

        Args:
            user: User whose membership should be loaded.
            course: Course whose membership should be loaded.

        Returns:
            The matching membership when found; otherwise, ``None``.
        """
        if course.id is None:
            raise ValueError("Course must be persisted before membership lookup")

        return self._session.get(Membership, (user.pid, course.id))

    def get_by_user_and_course_ids(self, user_pid: int, course_id: int) -> Membership | None:
        """Looks up a membership by user PID and course ID.

        Args:
            user_pid: PID of the user.
            course_id: Primary key of the course.

        Returns:
            The matching membership when found; otherwise, ``None``.
        """
        return self._session.get(Membership, (user_pid, course_id))

    def get_active_by_user(self, user: User) -> list[Membership]:
        """Returns all non-dropped memberships for a user.

        Args:
            user: User whose active memberships should be loaded.

        Returns:
            List of active memberships.
        """
        query = (
            select(Membership)
            .options(selectinload(Membership.course))  # type: ignore
            .where(
                col(Membership.user_pid) == user.pid,
                col(Membership.state) != MembershipState.DROPPED,
            )
        )
        return list(self._session.exec(query).all())

    def get_all_by_course(self, course: Course) -> list[Membership]:
        """Returns all memberships for a course.

        Args:
            course: Course whose memberships should be loaded.

        Returns:
            List of all memberships in the course.
        """
        if course.id is None:
            raise ValueError("Course must be persisted before membership lookup")

        query = select(Membership).where(
            col(Membership.course_id) == course.id,
        )
        return list(self._session.exec(query).all())

    def get_roster_page(
        self,
        course: Course,
        pagination: PaginationParams,
        query: str = "",
    ) -> PaginatedResult[Membership]:
        """Returns a paginated, optionally filtered roster for a course.

        Joins the ``User`` table so that search can match against user
        fields.  Results are eager-loaded with their related user.

        Args:
            course: Course whose roster should be returned.
            pagination: Page number and page size.
            query: Optional search string matched against given name,
                family name, PID (as text), or email via case-insensitive
                ``ILIKE``.

        Returns:
            A paginated result containing the matching memberships and
            the total count before pagination.
        """
        if course.id is None:
            raise ValueError("Course must be persisted before roster lookup")

        base = (
            select(Membership)
            .join(User, col(Membership.user_pid) == col(User.pid))
            .options(selectinload(Membership.user))  # type: ignore[arg-type]
            .where(col(Membership.course_id) == course.id)
        )

        if query:
            pattern = f"%{query}%"
            base = base.where(
                or_(
                    func.cast(col(User.pid), String).ilike(pattern),
                    col(User.given_name).ilike(pattern),
                    col(User.family_name).ilike(pattern),
                    col(User.email).ilike(pattern),
                )
            )

        count_query = select(func.count()).select_from(base.subquery())
        total: int = self._session.exec(count_query).one()

        offset = (pagination.page - 1) * pagination.page_size
        page_query = base.offset(offset).limit(pagination.page_size)
        items = list(self._session.exec(page_query).all())

        return PaginatedResult[Membership](
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
