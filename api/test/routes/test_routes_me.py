from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.di import get_authenticated_user, user_repository_factory
from api.main import app
from api.models import UpdateProfileRequest, UserProfile
from api.routes.me import get_current_subject_profile, update_current_subject_profile
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.tables.user import User


def _stub_user(
    *,
    pid: int = 123456789,
    name: str = "Test User",
    onyen: str = "testuser",
    email: str | None = None,
    family_name: str | None = "User",
    given_name: str | None = "Test",
) -> User:
    """Builds a stubbed domain user for route tests."""

    return User(
        pid=pid,
        name=name,
        onyen=onyen,
        email=email,
        family_name=family_name,
        given_name=given_name,
    )


def test_get_current_subject_profile_returns_user_profile() -> None:
    # Arrange
    user = _stub_user(email="test@example.com")

    # Act
    result = get_current_subject_profile(user)

    # Assert
    assert result == UserProfile(
        pid=user.pid,
        onyen="testuser",
        name="Test User",
        given_name="Test",
        family_name="User",
        email="test@example.com",
    )


def test_get_current_subject_profile_raises_validation_error_when_email_is_missing() -> (
    None
):
    # Arrange
    user = _stub_user(email=None)

    # Act / Assert
    with pytest.raises(ValidationError):
        get_current_subject_profile(user)


@pytest.mark.integration
def test_auth_me_returns_user_profile(client: TestClient) -> None:
    # Arrange
    user = _stub_user(email="test@example.com")
    app.dependency_overrides[get_authenticated_user] = lambda: user

    # Act
    response = client.get("/api/me")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Test User"
    assert body["given_name"] == "Test"
    assert body["family_name"] == "User"
    assert body["email"] == "test@example.com"


# --- update_current_subject_profile ---


def test_update_profile_updates_name_fields() -> None:
    # Arrange
    user = _stub_user(email="test@example.com")
    body = UpdateProfileRequest(given_name="Alice", family_name="Smith")
    user_repo = MagicMock(spec=UserRepository)
    updated_user = _stub_user(
        name="Alice Smith",
        given_name="Alice",
        family_name="Smith",
        email="test@example.com",
    )
    user_repo.update_user.return_value = updated_user

    # Act
    result = update_current_subject_profile(user, body, user_repo)

    # Assert
    assert result.given_name == "Alice"
    assert result.family_name == "Smith"
    assert result.name == "Alice Smith"
    user_repo.update_user.assert_called_once_with(user)


def test_update_profile_computes_full_name() -> None:
    # Arrange
    user = _stub_user(email="test@example.com")
    body = UpdateProfileRequest(given_name="Bob", family_name="Jones")
    user_repo = MagicMock(spec=UserRepository)
    user_repo.update_user.return_value = _stub_user(
        name="Bob Jones",
        given_name="Bob",
        family_name="Jones",
        email="test@example.com",
    )

    # Act
    result = update_current_subject_profile(user, body, user_repo)

    # Assert
    assert result.name == "Bob Jones"


@pytest.mark.integration
def test_put_me_updates_profile(client: TestClient) -> None:
    # Arrange
    user = _stub_user(email="test@example.com")
    app.dependency_overrides[get_authenticated_user] = lambda: user

    user_repo = MagicMock(spec=UserRepository)
    updated = _stub_user(
        name="Alice Smith",
        given_name="Alice",
        family_name="Smith",
        email="test@example.com",
    )
    user_repo.update_user.return_value = updated
    app.dependency_overrides[user_repository_factory] = lambda: user_repo

    # Act
    response = client.put(
        "/api/me",
        json={"given_name": "Alice", "family_name": "Smith"},
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["given_name"] == "Alice"
    assert body["family_name"] == "Smith"
    assert body["name"] == "Alice Smith"


@pytest.mark.integration
def test_auth_me_returns_401_without_token(client: TestClient) -> None:
    # Arrange (no overrides — HTTPBearer rejects missing credentials)

    # Act
    response = client.get("/api/me")

    # Assert
    assert response.status_code == 401
