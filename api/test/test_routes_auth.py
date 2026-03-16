from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.dependency_injection import (
    settings_factory,
    csxl_auth_service_factory,
)
from api.main import app
from api.routes.auth import (
    onyen_login_redirect,
    authenticate_with_csxl_callback,
)
from learnwithai.config import Settings
from learnwithai.models.user import User
from learnwithai.services.csxl_auth_service import AuthenticationException


# ---- helpers ----


def _stub_settings(**overrides) -> Settings:
    defaults = dict(
        host="localhost:8000",
        unc_auth_server_host="csxl.unc.edu",
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
    )
    defaults.update(overrides)
    return Settings.model_construct(_fields_set=None, **defaults)


def _stub_user(**overrides) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        name="Test User",
        pid="123456789",
        onyen="testuser",
    )
    defaults.update(overrides)
    return User.model_construct(_fields_set=None, **defaults)


# ---- onyen_login_redirect ----


def test_onyen_login_redirect_returns_307_to_auth_server() -> None:
    # Arrange
    settings = _stub_settings()

    # Act
    response = onyen_login_redirect(settings)

    # Assert
    assert response.status_code == 307
    assert "csxl.unc.edu/auth" in response.headers["location"]
    assert "origin=localhost:8000/auth" in response.headers["location"]


# ---- authenticate_with_csxl_callback ----


def test_authenticate_redirects_home_when_token_is_none() -> None:
    # Arrange
    session = MagicMock()
    csxl_auth_svc = MagicMock()

    # Act
    response = authenticate_with_csxl_callback(session, csxl_auth_svc, token=None)

    # Assert
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_authenticate_returns_401_when_token_verification_fails() -> None:
    # Arrange
    session = MagicMock()
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.verify_auth_token.side_effect = AuthenticationException()

    # Act / Assert
    with pytest.raises(Exception) as exc_info:
        authenticate_with_csxl_callback(session, csxl_auth_svc, token="bad-token")

    assert exc_info.value.status_code == 401  # type: ignore[union-attr]


def test_authenticate_returns_500_when_registration_fails() -> None:
    # Arrange
    session = MagicMock()
    session.begin.return_value.__enter__ = lambda s: s
    session.begin.return_value.__exit__ = lambda s, *a: None
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.verify_auth_token.return_value = ("testuser", "123456789")
    csxl_auth_svc.registered_user_from_onyen_pid.side_effect = AuthenticationException()

    # Act / Assert
    with pytest.raises(Exception) as exc_info:
        authenticate_with_csxl_callback(session, csxl_auth_svc, token="valid-token")

    assert exc_info.value.status_code == 500  # type: ignore[union-attr]


def test_authenticate_issues_jwt_and_redirects_on_success() -> None:
    # Arrange
    session = MagicMock()
    session.begin.return_value.__enter__ = lambda s: s
    session.begin.return_value.__exit__ = lambda s, *a: None
    user = _stub_user()
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.verify_auth_token.return_value = ("testuser", "123456789")
    csxl_auth_svc.registered_user_from_onyen_pid.return_value = user
    csxl_auth_svc.issue_jwt_token.return_value = "jwt-token-123"

    # Act
    response = authenticate_with_csxl_callback(
        session, csxl_auth_svc, token="valid-token"
    )

    # Assert
    assert response.status_code == 302
    assert response.headers["location"] == "/jwt?token=jwt-token-123"
    csxl_auth_svc.issue_jwt_token.assert_called_once_with(user)


# ---- integration tests via TestClient ----


@pytest.mark.integration
def test_onyen_endpoint_redirects_to_auth_server(client: TestClient) -> None:
    # Arrange
    settings = _stub_settings()
    app.dependency_overrides[settings_factory] = lambda: settings

    # Act
    response = client.get("/auth/onyen", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert "csxl.unc.edu/auth" in response.headers["location"]


@pytest.mark.integration
def test_auth_callback_redirects_home_without_token(client: TestClient) -> None:
    # Arrange (no overrides needed — token defaults to None)

    # Act
    response = client.get("/auth", follow_redirects=False)

    # Assert
    assert response.status_code == 302
    assert response.headers["location"] == "/"


@pytest.mark.integration
def test_auth_callback_returns_401_for_invalid_token(client: TestClient) -> None:
    # Arrange
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.verify_auth_token.side_effect = AuthenticationException()
    app.dependency_overrides[csxl_auth_service_factory] = lambda: csxl_auth_svc

    # Act
    response = client.get("/auth?token=bad-token")

    # Assert
    assert response.status_code == 401
