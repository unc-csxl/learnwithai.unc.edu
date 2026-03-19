"""Tests for the development-only API routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.dependency_injection import csxl_auth_service_factory
from api.main import app
from api.routes.dev import dev_login_as, dev_reset_db
from learnwithai.tables.user import User


# ---- helpers ----


def _stub_user(**overrides) -> User:
    """Create a stub User suitable for unit tests."""
    defaults = dict(
        pid=222222222,
        name="Ina Instructor",
        onyen="instructor",
        email="instructor@unc.edu",
        family_name="Instructor",
        given_name="Ina",
    )
    defaults.update(overrides)
    mock = MagicMock(spec=User)
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock  # type: ignore[return-value]


# ---- dev_login_as unit tests ----


def test_dev_login_as_returns_302_with_jwt_for_known_user() -> None:
    user = _stub_user()
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.get_user_by_pid.return_value = user
    csxl_auth_svc.issue_jwt_token.return_value = "dev-jwt-token"

    response = dev_login_as(222222222, csxl_auth_svc)

    assert response.status_code == 302
    assert response.headers["location"] == "/jwt?token=dev-jwt-token"
    csxl_auth_svc.get_user_by_pid.assert_called_once_with(222222222)
    csxl_auth_svc.issue_jwt_token.assert_called_once_with(user)


def test_dev_login_as_raises_404_for_unknown_user() -> None:
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.get_user_by_pid.return_value = None

    with pytest.raises(Exception) as exc_info:
        dev_login_as(999999999, csxl_auth_svc)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]


# ---- dev_reset_db unit tests ----


@patch("api.routes.dev.seed")
@patch("api.routes.dev.Session")
@patch("api.routes.dev.get_engine")
@patch("api.routes.dev.reset_db_and_tables")
def test_dev_reset_db_calls_reset_and_seed(
    mock_reset: MagicMock,
    mock_get_engine: MagicMock,
    mock_session_cls: MagicMock,
    mock_seed: MagicMock,
) -> None:
    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    result = dev_reset_db()

    mock_reset.assert_called_once()
    mock_seed.assert_called_once_with(mock_session)
    mock_session.commit.assert_called_once()
    assert result == {"detail": "Database reset and seeded."}


# ---- integration tests via TestClient ----


@pytest.mark.integration
def test_dev_login_endpoint_returns_302_for_known_user(client: TestClient) -> None:
    user = _stub_user(pid=222222222)
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.get_user_by_pid.return_value = user
    csxl_auth_svc.issue_jwt_token.return_value = "test-jwt"
    app.dependency_overrides[csxl_auth_service_factory] = lambda: csxl_auth_svc

    response = client.get("/api/auth/as/222222222", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/jwt?token=test-jwt"


@pytest.mark.integration
def test_dev_login_endpoint_returns_404_for_unknown_user(client: TestClient) -> None:
    csxl_auth_svc = MagicMock()
    csxl_auth_svc.get_user_by_pid.return_value = None
    app.dependency_overrides[csxl_auth_service_factory] = lambda: csxl_auth_svc

    response = client.get("/api/auth/as/999999999")

    assert response.status_code == 404


@pytest.mark.integration
@patch("api.routes.dev.seed")
@patch("api.routes.dev.Session")
@patch("api.routes.dev.get_engine")
@patch("api.routes.dev.reset_db_and_tables")
def test_dev_reset_db_endpoint(
    mock_reset: MagicMock,
    mock_get_engine: MagicMock,
    mock_session_cls: MagicMock,
    mock_seed: MagicMock,
    client: TestClient,
) -> None:
    mock_session = MagicMock()
    mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

    response = client.post("/api/dev/reset-db")

    assert response.status_code == 200
    assert response.json() == {"detail": "Database reset and seeded."}
