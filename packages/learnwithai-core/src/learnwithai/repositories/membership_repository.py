"""Persistence helpers for membership (user-course join) records."""

from sqlalchemy import String, func, or_
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from ..db import Session
from ..pagination import PaginatedResult, PaginationParams
from ..tables.course import Course
from ..tables.membership import Membership, MembershipState
from ..tables.user import User


class MembershipRepository:
    """Provides membership lookup and persistence operations."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session.

        Args:
            session: Session used to read and write membership records.
        """
        self._session = session

    def create(self, membership: Membership) -> Membership:
        """Persists a new membership and reloads database defaults.

        Args:
            membership: Membership instance to insert.

        Returns:
            The persisted membership with refreshed database state.
        """
        self._session.add(membership)
        self._session.flush()
        self._session.refresh(membership)
        return membership

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

    def update(self, membership: Membership) -> Membership:
        """Merges changes to an existing membership and refreshes state.

        Args:
            membership: Membership instance with updated fields.

        Returns:
            The updated membership with refreshed database state.
        """
        merged = self._session.merge(membership)
        self._session.flush()
        self._session.refresh(merged)
        return merged

    def delete(self, membership: Membership) -> None:
        """Deletes a membership.

        Args:
            membership: Membership instance to remove.
        """
        self._session.delete(membership)
        self._session.flush()

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
