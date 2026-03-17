from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.dependency_injection import get_current_user
from api.main import app
from api.models import UserProfile
from api.routes.me import get_current_user_profile
from learnwithai.models import User


def _stub_user(
    *,
    id: uuid.UUID | None = None,
    name: str = "Test User",
    pid: str = "123456789",
    onyen: str = "testuser",
    email: str | None = None,
    family_name: str | None = "User",
    given_name: str | None = "Test",
) -> User:
    """Builds a stubbed domain user for route tests."""

    return User(
        id=id or uuid.uuid4(),
        name=name,
        pid=pid,
        onyen=onyen,
        email=email,
        family_name=family_name,
        given_name=given_name,
    )


def test_get_current_user_profile_returns_user_profile() -> None:
    # Arrange
    user = _stub_user(email="test@example.com")

    # Act
    result = get_current_user_profile(user)

    # Assert
    assert result == UserProfile(
        id=str(user.id),
        name="Test User",
        given_name="Test",
        family_name="User",
        email="test@example.com",
    )


def test_get_current_user_profile_raises_validation_error_when_email_is_missing() -> (
    None
):
    # Arrange
    user = _stub_user(email=None)

    # Act / Assert
    with pytest.raises(ValidationError):
        get_current_user_profile(user)


@pytest.mark.integration
def test_auth_me_returns_user_profile(client: TestClient) -> None:
    # Arrange
    user = _stub_user(email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    # Act
    response = client.get("/api/me")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Test User"
    assert body["given_name"] == "Test"
    assert body["family_name"] == "User"
    assert body["email"] == "test@example.com"


@pytest.mark.integration
def test_auth_me_returns_401_without_token(client: TestClient) -> None:
    # Arrange (no overrides — real get_current_user will reject)

    # Act
    response = client.get("/api/me")

    # Assert
    assert response.status_code == 401
