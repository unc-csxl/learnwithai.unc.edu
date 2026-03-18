from __future__ import annotations

import pytest
from sqlmodel import Session

from learnwithai.tables.course import Course
from learnwithai.repositories.course_repository import CourseRepository


# --- create ---


@pytest.mark.integration
def test_create_persists_and_returns_course(session: Session) -> None:
    # Arrange
    repo = CourseRepository(session)
    course = Course(name="Intro to CS", term="Fall 2026", section="001")

    # Act
    result = repo.create(course)

    # Assert
    assert result.id is not None
    assert result.name == "Intro to CS"
    assert result.term == "Fall 2026"
    assert result.section == "001"
    assert result.created_at is not None
    assert result.updated_at is not None


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_course_when_exists(session: Session) -> None:
    # Arrange
    repo = CourseRepository(session)
    course = repo.create(Course(name="Algorithms", term="Spring 2027", section="002"))

    # Act
    result = repo.get_by_id(course.id)  # type: ignore[arg-type]

    # Assert
    assert result is not None
    assert result.name == "Algorithms"


@pytest.mark.integration
def test_get_by_id_returns_none_when_not_found(session: Session) -> None:
    # Arrange
    repo = CourseRepository(session)

    # Act
    result = repo.get_by_id(999999)

    # Assert
    assert result is None


# --- update ---


@pytest.mark.integration
def test_update_modifies_course(session: Session) -> None:
    # Arrange
    repo = CourseRepository(session)
    course = repo.create(Course(name="Old Name", term="Fall 2026", section="001"))
    course.name = "New Name"

    # Act
    result = repo.update(course)

    # Assert
    assert result.name == "New Name"
    fetched = repo.get_by_id(course.id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.name == "New Name"


# --- delete ---


@pytest.mark.integration
def test_delete_removes_course(session: Session) -> None:
    # Arrange
    repo = CourseRepository(session)
    course = repo.create(Course(name="To Delete", term="Fall 2026", section="001"))
    course_id = course.id

    # Act
    repo.delete(course)

    # Assert
    assert repo.get_by_id(course_id) is None  # type: ignore[arg-type]
