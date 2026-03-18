from __future__ import annotations

import pytest
from sqlmodel import Session

from learnwithai.tables.course import Course
from learnwithai.tables.membership import Membership, MembershipState, MembershipType
from learnwithai.repositories.membership_repository import MembershipRepository


def _seed_course(session: Session) -> Course:
    course = Course(name="Intro to CS", term="Fall 2026", section="001")
    session.add(course)
    session.flush()
    return course


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
    result = repo.get_by_user_and_course(123456789, course.id)  # type: ignore[arg-type]

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
    assert repo.get_by_user_and_course(123456789, course.id) is None  # type: ignore[arg-type]
