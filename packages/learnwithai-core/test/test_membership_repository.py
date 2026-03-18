from __future__ import annotations

import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

from learnwithai.tables.course import Course
from learnwithai.tables.membership import Membership, MembershipState, MembershipType
from learnwithai.tables.user import User
from learnwithai.repositories.membership_repository import MembershipRepository

DEFAULT_TEST_DB_URL = (
    "postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai_test"
)
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)


@pytest.fixture()
def session():
    """Provide a transactional session that rolls back after each test."""
    engine = create_engine(TEST_DB_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        session.rollback()


def _seed_user(session: Session, pid: int = 123456789) -> User:
    user = User(pid=pid, name="Test User", onyen="testuser")
    session.add(user)
    session.flush()
    return user


def _seed_course(session: Session) -> Course:
    course = Course(name="Intro to CS", term="Fall 2026", section="001")
    session.add(course)
    session.flush()
    return course


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_membership(session: Session) -> None:
    # Arrange
    user = _seed_user(session)
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = Membership(
        user_pid=user.pid,
        course_id=course.id,  # type: ignore[arg-type]
        type=MembershipType.STUDENT,
        state=MembershipState.ENROLLED,
    )

    # Act
    result = repo.create(membership)

    # Assert
    assert result.id is not None
    assert result.user_pid == user.pid
    assert result.course_id == course.id
    assert result.type == MembershipType.STUDENT
    assert result.state == MembershipState.ENROLLED


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_membership_when_exists(session: Session) -> None:
    # Arrange
    user = _seed_user(session)
    course = _seed_course(session)
    repo = MembershipRepository(session)
    created = repo.create(
        Membership(
            user_pid=user.pid,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.INSTRUCTOR,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_by_id(created.id)  # type: ignore[arg-type]

    # Assert
    assert result is not None
    assert result.type == MembershipType.INSTRUCTOR


@pytest.mark.integration
def test_get_by_id_returns_none_when_not_found(session: Session) -> None:
    # Arrange
    repo = MembershipRepository(session)

    # Act
    result = repo.get_by_id(999999)

    # Assert
    assert result is None


# --- get_by_user_and_course ---


@pytest.mark.integration
def test_get_by_user_and_course_returns_membership(session: Session) -> None:
    # Arrange
    user = _seed_user(session)
    course = _seed_course(session)
    repo = MembershipRepository(session)
    repo.create(
        Membership(
            user_pid=user.pid,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.TA,
            state=MembershipState.ENROLLED,
        )
    )

    # Act
    result = repo.get_by_user_and_course(user.pid, course.id)  # type: ignore[arg-type]

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
    result = repo.get_by_user_and_course(999999999, 999999)

    # Assert
    assert result is None


# --- update ---


@pytest.mark.integration
def test_update_changes_membership_state(session: Session) -> None:
    # Arrange
    user = _seed_user(session)
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = repo.create(
        Membership(
            user_pid=user.pid,
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
    user = _seed_user(session)
    course = _seed_course(session)
    repo = MembershipRepository(session)
    membership = repo.create(
        Membership(
            user_pid=user.pid,
            course_id=course.id,  # type: ignore[arg-type]
            type=MembershipType.STUDENT,
            state=MembershipState.ENROLLED,
        )
    )
    membership_id = membership.id

    # Act
    repo.delete(membership_id)  # type: ignore[arg-type]

    # Assert
    assert repo.get_by_id(membership_id) is None  # type: ignore[arg-type]


@pytest.mark.integration
def test_delete_does_nothing_when_not_found(session: Session) -> None:
    # Arrange
    repo = MembershipRepository(session)

    # Act / Assert — should not raise
    repo.delete(999999)
