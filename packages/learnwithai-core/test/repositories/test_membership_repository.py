from __future__ import annotations

import pytest
from learnwithai.pagination import PaginationParams
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.tables.course import Course, Term
from learnwithai.tables.membership import Membership, MembershipState, MembershipType
from learnwithai.tables.user import User
from sqlalchemy import inspect
from sqlmodel import Session


def _seed_course(session: Session) -> Course:
    course = Course(course_number="COMP101", name="Intro to CS", term=Term.FALL, year=2026)
    session.add(course)
    session.flush()
    return course


def _make_user(pid: int) -> User:
    return User.model_construct(
        _fields_set=None,
        pid=pid,
        name="Test User",
        onyen=f"user{pid}",
    )


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_membership(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = Membership(
        user_pid=123456789,
        course_id=course.id,  # type: ignore[arg-type]
        type=MembershipType.STUDENT,
        state=MembershipState.ENROLLED,
    )

    # Act
    result = repo.create(membership)

    # Assert
    assert result.user_pid == 123456789
    assert result.course_id == course.id
    assert result.type == MembershipType.STUDENT
    assert result.state == MembershipState.ENROLLED


# --- get_by_user_and_course ---


@pytest.mark.integration
def test_get_by_user_and_course_returns_membership(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=123456789,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.TA,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_by_user_and_course(_make_user(123456789), course)

    # Assert
    assert result is not None
    assert result.type == MembershipType.TA


@pytest.mark.integration
def test_get_by_user_and_course_returns_none_when_not_found(
    session: Session,
) -> None:
    # Arrange
    repo = MembershipRepository(session)

    # Act
    missing_course = Course.model_construct(
        _fields_set=None,
        id=999999,
        course_number="COMP999",
        name="Missing",
        description="",
        term=Term.FALL,
        year=2026,
    )
    result = repo.get_by_user_and_course(_make_user(999999999), missing_course)

    # Assert
    assert result is None


@pytest.mark.integration
def test_get_by_user_and_course_raises_for_unpersisted_course(session: Session) -> None:
    # Arrange
    repo = MembershipRepository(session)
    missing_id_course = Course(course_number="COMP999", name="Draft", term=Term.FALL, year=2026)

    # Act / Assert
    with pytest.raises(ValueError, match="Course must be persisted"):
        repo.get_by_user_and_course(_make_user(123456789), missing_id_course)


# --- get_by_user_and_course_ids ---


@pytest.mark.integration
def test_get_by_id_returns_membership_for_composite_key(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    created = repo.create(
        Membership(
            user_pid=123456789,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_by_id((created.user_pid, created.course_id))

    # Assert
    assert result is not None
    assert result.user_pid == created.user_pid
    assert result.course_id == created.course_id


@pytest.mark.integration
def test_get_by_user_and_course_ids_returns_membership(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=123456789,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_by_user_and_course_ids(123456789, course.id)  # type: ignore[arg-type]

    # Assert
    assert result is not None
    assert result.user_pid == 123456789
    assert result.type == MembershipType.STUDENT


@pytest.mark.integration
def test_get_by_user_and_course_ids_returns_none_when_not_found(
    session: Session,
) -> None:
    # Arrange
    repo = MembershipRepository(session)

    # Act
    result = repo.get_by_user_and_course_ids(999999999, 999999)

    # Assert
    assert result is None


# --- create with pending default ---


@pytest.mark.integration
def test_create_defaults_to_pending_state(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = Membership(
        user_pid=111222333,
        course_id=course.id,  # type: ignore[arg-type]
        type=MembershipType.STUDENT,
    )

    # Act
    result = repo.create(membership)

    # Assert
    assert result.state == MembershipState.PENDING


# --- create without corresponding user (orphan allowed) ---


@pytest.mark.integration
def test_create_allows_orphaned_user_pid(session: Session) -> None:
    # Arrange — no user with pid 999888777 exists
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = Membership(
        user_pid=999888777,
        course_id=course.id,  # type: ignore[arg-type]
        type=MembershipType.STUDENT,
        state=MembershipState.PENDING,
    )

    # Act
    result = repo.create(membership)

    # Assert
    assert result.user_pid == 999888777


# --- update ---


@pytest.mark.integration
def test_update_changes_membership_state(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = repo.create(
        Membership(
            user_pid=123456789,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )
    membership.state = MembershipState.DROPPED

    # Act
    result = repo.update(membership)

    # Assert
    assert result.state == MembershipState.DROPPED


# --- delete ---


@pytest.mark.integration
def test_delete_removes_membership(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = repo.create(
        Membership(
            user_pid=123456789,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    repo.delete(membership)

    # Assert
    assert repo.get_by_user_and_course(_make_user(123456789), course) is None


# --- get_active_by_user ---


@pytest.mark.integration
def test_get_active_by_user_returns_non_dropped(session: Session) -> None:
    # Arrange
    c1 = _seed_course(session)
    c2 = Course(course_number="COMP301", name="Algorithms", term=Term.SPRING, year=2027)
    session.add(c2)
    session.flush()
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=123456789,
            course_id=c1.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )
    repo.create(
        Membership(
            user_pid=123456789,
            course_id=c2.id,  # type: ignore[arg-type]
            type=MembershipType.TA,
            state=MembershipState.DROPPED,
        )
    )

    # Act
    result = repo.get_active_by_user(_make_user(123456789))

    # Assert
    assert len(result) == 1
    assert result[0].course_id == c1.id
    assert result[0].course is not None
    assert result[0].course.name == c1.name
    state = inspect(result[0])
    assert state is not None
    assert "course" not in state.unloaded


@pytest.mark.integration
def test_get_active_by_user_includes_pending(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=123456789,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.PENDING,
        )
    )

    # Act
    result = repo.get_active_by_user(_make_user(123456789))

    # Assert
    assert len(result) == 1
    assert result[0].state == MembershipState.PENDING


# --- get_all_by_course ---


@pytest.mark.integration
def test_get_all_by_course_returns_all_memberships(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=111111111,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.INSTRUCTOR,
            state=MembershipState.ENROLLED,
        )
    )
    repo.create(
        Membership(
            user_pid=222222222,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_all_by_course(course)

    # Assert
    assert len(result) == 2


@pytest.mark.integration
def test_get_all_by_course_raises_for_unpersisted_course(session: Session) -> None:
    # Arrange
    repo = MembershipRepository(session)
    missing_id_course = Course(course_number="COMP999", name="Draft", term=Term.FALL, year=2026)

    # Act / Assert
    with pytest.raises(ValueError, match="Course must be persisted"):
        repo.get_all_by_course(missing_id_course)


# --- get_roster_page ---


def _seed_user(session: Session, pid: int, given: str, family: str, email: str) -> User:
    user = User(
        pid=pid,
        name=f"{given} {family}",
        onyen=f"user{pid}",
        given_name=given,
        family_name=family,
        email=email,
    )
    session.add(user)
    session.flush()
    return user


@pytest.mark.integration
def test_get_roster_page_returns_paginated_members(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    u1 = _seed_user(session, 100, "Alice", "Alpha", "alice@unc.edu")
    u2 = _seed_user(session, 200, "Bob", "Bravo", "bob@unc.edu")
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=u1.pid,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )
    repo.create(
        Membership(
            user_pid=u2.pid,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.TA,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_roster_page(course, PaginationParams(page=1, page_size=25))

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert result.page == 1


@pytest.mark.integration
def test_get_roster_page_paginates(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    for i in range(3):
        u = _seed_user(session, 100 + i, f"U{i}", "Last", f"u{i}@unc.edu")
        repo = MembershipRepository(session)
        repo.create(
            Membership(
                user_pid=u.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.STUDENT,
                state=MembershipState.ENROLLED,
            )
        )

    # Act
    repo = MembershipRepository(session)
    result = repo.get_roster_page(course, PaginationParams(page=1, page_size=2))

    # Assert
    assert result.total == 3
    assert len(result.items) == 2
    assert result.page == 1
    assert result.page_size == 2


@pytest.mark.integration
def test_get_roster_page_filters_by_name(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    u1 = _seed_user(session, 100, "Alice", "Alpha", "alice@unc.edu")
    u2 = _seed_user(session, 200, "Bob", "Bravo", "bob@unc.edu")
    repo = MembershipRepository(session)
    for u in [u1, u2]:
        repo.create(
            Membership(
                user_pid=u.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.STUDENT,
                state=MembershipState.ENROLLED,
            )
        )

    # Act
    result = repo.get_roster_page(course, PaginationParams(), "alice")

    # Assert
    assert result.total == 1
    assert result.items[0].user_pid == 100


@pytest.mark.integration
def test_get_roster_page_filters_by_email(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    u1 = _seed_user(session, 100, "Alice", "Alpha", "alice@unc.edu")
    u2 = _seed_user(session, 200, "Bob", "Bravo", "bob@unc.edu")
    repo = MembershipRepository(session)
    for u in [u1, u2]:
        repo.create(
            Membership(
                user_pid=u.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.STUDENT,
                state=MembershipState.ENROLLED,
            )
        )

    # Act
    result = repo.get_roster_page(course, PaginationParams(), "bob@")

    # Assert
    assert result.total == 1
    assert result.items[0].user_pid == 200


@pytest.mark.integration
def test_get_roster_page_filters_by_pid(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    u1 = _seed_user(session, 100, "Alice", "Alpha", "alice@unc.edu")
    u2 = _seed_user(session, 200, "Bob", "Bravo", "bob@unc.edu")
    repo = MembershipRepository(session)
    for u in [u1, u2]:
        repo.create(
            Membership(
                user_pid=u.pid,
                course_id=course.id,  # type: ignore[arg-type]
                type=MembershipType.STUDENT,
                state=MembershipState.ENROLLED,
            )
        )

    # Act
    result = repo.get_roster_page(course, PaginationParams(), "200")

    # Assert
    assert result.total == 1
    assert result.items[0].user_pid == 200


@pytest.mark.integration
def test_get_roster_page_eager_loads_user(session: Session) -> None:
    # Arrange
    course = _seed_course(session)
    u = _seed_user(session, 100, "Alice", "Alpha", "alice@unc.edu")
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=u.pid,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_roster_page(course, PaginationParams())

    # Assert
    member = result.items[0]
    state = inspect(member)
    assert state is not None
    assert "user" not in state.unloaded
    assert member.user.given_name == "Alice"


@pytest.mark.integration
def test_get_roster_page_raises_for_unpersisted_course(session: Session) -> None:
    # Arrange
    repo = MembershipRepository(session)
    draft = Course(course_number="COMP999", name="Draft", term=Term.FALL, year=2026)

    # Act / Assert
    with pytest.raises(ValueError, match="Course must be persisted"):
        repo.get_roster_page(draft, PaginationParams())
