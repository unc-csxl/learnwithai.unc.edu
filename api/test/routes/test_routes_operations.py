# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for operations routes (operator CRUD and impersonation)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from learnwithai.errors import AuthorizationError
from learnwithai.tables.operator import OperatorRole

from api.di import (
    get_authenticated_user,
    operator_service_factory,
    user_repository_factory,
)
from api.main import app
from api.models import (
    GrantOperatorRequest,
    ImpersonationTokenResponse,
    OperatorResponse,
    UpdateOperatorRoleRequest,
)
from api.routes.operations import (
    grant_operator,
    impersonate_user,
    list_operators,
    revoke_operator,
    search_users,
    update_operator_role,
)

# ---- helpers ----


def _stub_user(
    *,
    pid: int = 111111111,
    name: str = "Admin User",
    onyen: str = "admin",
    email: str = "admin@unc.edu",
) -> MagicMock:
    mock = MagicMock()
    mock.pid = pid
    mock.name = name
    mock.onyen = onyen
    mock.email = email
    return mock


def _stub_operator(
    *,
    user_pid: int = 111111111,
    role: OperatorRole = OperatorRole.SUPERADMIN,
    name: str = "Admin User",
    email: str = "admin@unc.edu",
    created_by_pid: int | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.user_pid = user_pid
    mock.role = role
    mock.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock.created_by_pid = created_by_pid
    user = MagicMock()
    user.name = name
    user.email = email
    mock.user = user
    return mock


# ---- list_operators (unit) ----


def test_list_operators_returns_operator_list() -> None:
    subject = _stub_user()
    operator_svc = MagicMock()
    ops = [
        _stub_operator(user_pid=111111111, role=OperatorRole.SUPERADMIN),
        _stub_operator(user_pid=222222222, role=OperatorRole.ADMIN, name="Other Admin"),
    ]
    operator_svc.list_operators.return_value = ops

    result = list_operators(subject, operator_svc)

    assert len(result) == 2
    assert all(isinstance(r, OperatorResponse) for r in result)
    assert result[0].role == OperatorRole.SUPERADMIN
    assert result[1].role == OperatorRole.ADMIN
    operator_svc.list_operators.assert_called_once_with(subject)


# ---- grant_operator (unit) ----


def test_grant_operator_returns_operator_response() -> None:
    subject = _stub_user()
    target = _stub_user(pid=222222222, name="Target", email="target@unc.edu")
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()
    created_op = _stub_operator(user_pid=222222222, role=OperatorRole.ADMIN, name="Target", email="target@unc.edu")
    operator_svc.grant_operator.return_value = created_op
    body = GrantOperatorRequest(user_pid=222222222, role=OperatorRole.ADMIN)

    result = grant_operator(subject, body, operator_svc, user_repo)

    assert isinstance(result, OperatorResponse)
    assert result.user_pid == 222222222
    assert result.role == OperatorRole.ADMIN


def test_grant_operator_raises_404_for_missing_user() -> None:
    subject = _stub_user()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    operator_svc = MagicMock()
    body = GrantOperatorRequest(user_pid=999999999, role=OperatorRole.HELPDESK)

    with pytest.raises(Exception) as exc_info:
        grant_operator(subject, body, operator_svc, user_repo)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]


def test_grant_operator_raises_409_when_already_operator() -> None:
    subject = _stub_user()
    target = _stub_user(pid=222222222)
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()
    operator_svc.grant_operator.side_effect = ValueError("User is already an operator.")
    body = GrantOperatorRequest(user_pid=222222222, role=OperatorRole.ADMIN)

    with pytest.raises(Exception) as exc_info:
        grant_operator(subject, body, operator_svc, user_repo)

    assert exc_info.value.status_code == 409  # type: ignore[union-attr]


# ---- update_operator_role (unit) ----


def test_update_operator_role_returns_updated_response() -> None:
    subject = _stub_user()
    target = _stub_user(pid=222222222, name="Target", email="target@unc.edu")
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()
    updated = _stub_operator(user_pid=222222222, role=OperatorRole.ADMIN, name="Target", email="target@unc.edu")
    operator_svc.update_operator_role.return_value = updated
    body = UpdateOperatorRoleRequest(role=OperatorRole.ADMIN)

    result = update_operator_role(subject, 222222222, body, operator_svc, user_repo)

    assert isinstance(result, OperatorResponse)
    assert result.role == OperatorRole.ADMIN


def test_update_operator_role_raises_404_for_missing_user() -> None:
    subject = _stub_user()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    operator_svc = MagicMock()
    body = UpdateOperatorRoleRequest(role=OperatorRole.ADMIN)

    with pytest.raises(Exception) as exc_info:
        update_operator_role(subject, 999999999, body, operator_svc, user_repo)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]


def test_update_operator_role_raises_404_when_not_operator() -> None:
    """When the target user exists but is not an operator, the service raises ValueError."""
    subject = _stub_user()
    target = _stub_user(pid=222222222, name="Target", email="target@unc.edu")
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()
    operator_svc.update_operator_role.side_effect = ValueError("User is not an operator.")
    body = UpdateOperatorRoleRequest(role=OperatorRole.ADMIN)

    with pytest.raises(Exception) as exc_info:
        update_operator_role(subject, 222222222, body, operator_svc, user_repo)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]


# ---- revoke_operator (unit) ----


def test_revoke_operator_returns_204() -> None:
    subject = _stub_user()
    target = _stub_user(pid=222222222)
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()

    result = revoke_operator(subject, 222222222, operator_svc, user_repo)

    assert result is None
    operator_svc.revoke_operator.assert_called_once_with(subject, target)


def test_revoke_operator_raises_404_for_missing_user() -> None:
    subject = _stub_user()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    operator_svc = MagicMock()

    with pytest.raises(Exception) as exc_info:
        revoke_operator(subject, 999999999, operator_svc, user_repo)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]


def test_revoke_operator_raises_409_for_self_revocation() -> None:
    subject = _stub_user()
    target = _stub_user(pid=222222222)
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()
    operator_svc.revoke_operator.side_effect = ValueError("Cannot revoke your own operator access.")

    with pytest.raises(Exception) as exc_info:
        revoke_operator(subject, 222222222, operator_svc, user_repo)

    assert exc_info.value.status_code == 409  # type: ignore[union-attr]


# ---- impersonate_user (unit) ----


def test_impersonate_user_returns_token() -> None:
    subject = _stub_user()
    target = _stub_user(pid=222222222)
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = target
    operator_svc = MagicMock()
    operator_svc.issue_impersonation_token.return_value = "fake.jwt.token"
    settings = MagicMock()

    result = impersonate_user(subject, 222222222, operator_svc, user_repo, settings)

    assert isinstance(result, ImpersonationTokenResponse)
    assert result.token == "fake.jwt.token"


def test_impersonate_user_raises_404_for_missing_user() -> None:
    subject = _stub_user()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None
    operator_svc = MagicMock()
    settings = MagicMock()

    with pytest.raises(Exception) as exc_info:
        impersonate_user(subject, 999999999, operator_svc, user_repo, settings)

    assert exc_info.value.status_code == 404  # type: ignore[union-attr]


# ---- integration tests via TestClient ----


@pytest.mark.integration
def test_list_operators_endpoint(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_svc = MagicMock()
    mock_svc.list_operators.return_value = [
        _stub_operator(user_pid=111111111, role=OperatorRole.SUPERADMIN),
    ]
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc

    response = client.get("/api/operations/operators")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user_pid"] == 111111111
    assert body[0]["role"] == "superadmin"


@pytest.mark.integration
def test_list_operators_returns_403_for_non_operator(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_svc = MagicMock()
    mock_svc.list_operators.side_effect = AuthorizationError("Operator access required.")
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc

    response = client.get("/api/operations/operators")

    assert response.status_code == 403


@pytest.mark.integration
def test_grant_operator_endpoint(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    target = _stub_user(pid=222222222, name="Target", email="target@unc.edu")
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = target
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo
    created = _stub_operator(user_pid=222222222, role=OperatorRole.ADMIN, name="Target", email="target@unc.edu")
    mock_svc = MagicMock()
    mock_svc.grant_operator.return_value = created
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc

    response = client.post(
        "/api/operations/operators",
        json={"user_pid": 222222222, "role": "admin"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_pid"] == 222222222
    assert body["role"] == "admin"


@pytest.mark.integration
def test_update_operator_role_endpoint(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    target = _stub_user(pid=222222222, name="Target", email="target@unc.edu")
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = target
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo
    updated = _stub_operator(user_pid=222222222, role=OperatorRole.ADMIN, name="Target", email="target@unc.edu")
    mock_svc = MagicMock()
    mock_svc.update_operator_role.return_value = updated
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc

    response = client.put(
        "/api/operations/operators/222222222",
        json={"role": "admin"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"


@pytest.mark.integration
def test_revoke_operator_endpoint(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    target = _stub_user(pid=222222222)
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = target
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo
    mock_svc = MagicMock()
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc

    response = client.delete("/api/operations/operators/222222222")

    assert response.status_code == 204
    mock_svc.revoke_operator.assert_called_once()


@pytest.mark.integration
def test_impersonate_endpoint(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    target = _stub_user(pid=222222222)
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_pid.return_value = target
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo
    mock_svc = MagicMock()
    mock_svc.issue_impersonation_token.return_value = "impersonation.jwt.token"
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc

    response = client.post("/api/operations/impersonate/222222222")

    assert response.status_code == 200
    body = response.json()
    assert body["token"] == "impersonation.jwt.token"


@pytest.mark.integration
def test_admin_routes_return_401_without_token(client: TestClient) -> None:
    response = client.get("/api/operations/operators")
    assert response.status_code == 401


# ---- search_users (unit) ----


def test_search_users_returns_results() -> None:
    subject = _stub_user()
    operator_svc = MagicMock()
    user_repo = MagicMock()
    target = _stub_user(pid=222222222, name="Sally Student", email="sally@unc.edu")
    user_repo.search_users.return_value = [target]

    result = search_users(subject, "Sally", operator_svc, user_repo)

    assert len(result) == 1
    assert result[0].pid == 222222222
    assert result[0].name == "Sally Student"
    operator_svc.require_permission.assert_called_once()


def test_search_users_raises_for_unauthorized() -> None:
    subject = _stub_user()
    operator_svc = MagicMock()
    operator_svc.require_permission.side_effect = AuthorizationError("Forbidden")
    user_repo = MagicMock()

    with pytest.raises(AuthorizationError):
        search_users(subject, "test", operator_svc, user_repo)


@pytest.mark.integration
def test_search_users_endpoint(client: TestClient) -> None:
    user = _stub_user()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    mock_svc = MagicMock()
    app.dependency_overrides[operator_service_factory] = lambda: mock_svc
    mock_user_repo = MagicMock()
    target = _stub_user(pid=222222222, name="Sally Student", email="sally@unc.edu")
    mock_user_repo.search_users.return_value = [target]
    app.dependency_overrides[user_repository_factory] = lambda: mock_user_repo

    response = client.get("/api/operations/users/search?q=Sally")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Sally Student"
