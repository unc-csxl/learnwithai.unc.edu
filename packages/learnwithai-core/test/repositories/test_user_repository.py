from __future__ import annotations

import pytest
from sqlmodel import Session

from learnwithai.tables.user import User
from learnwithai.repositories.user_repository import UserRepository


# --- get_by_pid ---


@pytest.mark.integration
def test_get_by_pid_returns_none_when_no_user_exists(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)

    # Act
    result = repo.get_by_pid(999999999)

    # Assert
    assert result is None


@pytest.mark.integration
def test_get_by_pid_returns_user_when_exists(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)
    user = User(pid=123456789, name="Test User", onyen="testuser")
    session.add(user)
    session.flush()

    # Act
    result = repo.get_by_pid(123456789)

    # Assert
    assert result is not None
    assert result.pid == 123456789
    assert result.name == "Test User"


# --- register_user ---


@pytest.mark.integration
def test_register_user_persists_and_returns_user(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)
    new_user = User(pid=987654321, name="New User", onyen="newuser")

    # Act
    result = repo.register_user(new_user)

    # Assert
    assert result.pid == 987654321
    assert result.name == "New User"
    fetched = repo.get_by_pid(987654321)
    assert fetched is not None
    assert fetched.pid == result.pid
