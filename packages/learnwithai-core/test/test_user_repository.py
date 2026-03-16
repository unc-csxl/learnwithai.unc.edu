from __future__ import annotations

import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

from learnwithai.models.user import User
from learnwithai.repositories.user_repository import UserRepository

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


# --- get_by_pid ---


@pytest.mark.integration
def test_get_by_pid_returns_none_when_no_user_exists(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)

    # Act
    result = repo.get_by_pid("nonexistent")

    # Assert
    assert result is None


@pytest.mark.integration
def test_get_by_pid_returns_user_when_exists(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)
    user = User(name="Test User", pid="123456789", onyen="testuser")
    session.add(user)
    session.flush()

    # Act
    result = repo.get_by_pid("123456789")

    # Assert
    assert result is not None
    assert result.pid == "123456789"
    assert result.name == "Test User"


# --- register_user ---


@pytest.mark.integration
def test_register_user_persists_and_returns_user(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)
    new_user = User(name="New User", pid="987654321", onyen="newuser")

    # Act
    result = repo.register_user(new_user)

    # Assert
    assert result.id is not None
    assert result.pid == "987654321"
    assert result.name == "New User"
    fetched = repo.get_by_pid("987654321")
    assert fetched is not None
    assert fetched.id == result.id


# --- get_by_id ---


@pytest.mark.integration
def test_get_by_id_returns_none_when_no_user_exists(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)

    # Act
    result = repo.get_by_id("00000000-0000-0000-0000-000000000000")

    # Assert
    assert result is None


@pytest.mark.integration
def test_get_by_id_returns_user_when_exists(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)
    user = User(name="Test User", pid="111222333", onyen="testid")
    session.add(user)
    session.flush()

    # Act
    result = repo.get_by_id(str(user.id))

    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.name == "Test User"
