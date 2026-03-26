from __future__ import annotations

import pytest
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.tables.user import User
from sqlmodel import Session

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


# --- list_all ---


@pytest.mark.integration
def test_list_all_returns_empty_when_no_users(session: Session) -> None:
    repo = UserRepository(session)

    result = repo.list_all()

    assert result == []


@pytest.mark.integration
def test_list_all_returns_all_users(session: Session) -> None:
    repo = UserRepository(session)
    session.add(User(pid=100000001, name="User A", onyen="usera"))
    session.add(User(pid=100000002, name="User B", onyen="userb"))
    session.flush()

    result = repo.list_all()

    assert len(result) == 2
    pids = {u.pid for u in result}
    assert pids == {100000001, 100000002}


# --- update_user ---


@pytest.mark.integration
def test_update_user_persists_changes(session: Session) -> None:
    # Arrange
    repo = UserRepository(session)
    user = User(pid=123456789, name="Old Name", onyen="testuser")
    session.add(user)
    session.flush()

    # Act
    user.name = "New Name"
    user.given_name = "New"
    user.family_name = "Name"
    result = repo.update_user(user)

    # Assert
    assert result.name == "New Name"
    assert result.given_name == "New"
    assert result.family_name == "Name"
    fetched = repo.get_by_pid(123456789)
    assert fetched is not None
    assert fetched.name == "New Name"
