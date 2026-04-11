# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for OperatorService."""

from __future__ import annotations

from unittest.mock import MagicMock

import jwt
import pytest
from learnwithai.errors import AuthorizationError
from learnwithai.repositories.operator_repository import OperatorRepository
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.services.operator_service import OperatorService
from learnwithai.tables.operator import (
    Operator,
    OperatorPermission,
    OperatorRole,
)
from learnwithai.tables.user import User


def _build_service(
    operator_repo: MagicMock | None = None,
    user_repo: MagicMock | None = None,
) -> OperatorService:
    return OperatorService(
        operator_repo=operator_repo or MagicMock(spec=OperatorRepository),
        user_repo=user_repo or MagicMock(spec=UserRepository),
    )


def _make_user(pid: int = 111111111) -> MagicMock:
    m = MagicMock(spec=User)
    m.pid = pid
    return m


def _make_operator(
    pid: int = 111111111,
    role: OperatorRole = OperatorRole.SUPERADMIN,
) -> MagicMock:
    m = MagicMock(spec=Operator)
    m.user_pid = pid
    m.role = role
    return m


def _make_settings() -> MagicMock:
    m = MagicMock()
    m.jwt_secret = "test-secret-key"
    m.jwt_algorithm = "HS256"
    return m


# --- get_operator ---


def test_get_operator_returns_operator_when_exists() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    expected = _make_operator()
    operator_repo.get_by_id.return_value = expected

    svc = _build_service(operator_repo)
    result = svc.get_operator(_make_user())

    assert result is expected


def test_get_operator_returns_none_when_not_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    operator_repo.get_by_id.return_value = None

    svc = _build_service(operator_repo)
    result = svc.get_operator(_make_user())

    assert result is None


# --- require_operator ---


def test_require_operator_returns_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    expected = _make_operator()
    operator_repo.get_by_id.return_value = expected

    svc = _build_service(operator_repo)
    result = svc.require_operator(_make_user())

    assert result is expected


def test_require_operator_raises_when_not_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    operator_repo.get_by_id.return_value = None

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Operator access required"):
        svc.require_operator(_make_user())


# --- require_permission ---


def test_require_permission_returns_operator_with_matching_permission() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    op = _make_operator(role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.return_value = op

    svc = _build_service(operator_repo)
    result = svc.require_permission(_make_user(), OperatorPermission.IMPERSONATE)

    assert result is op


def test_require_permission_raises_when_missing_permission() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    op = _make_operator(role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.return_value = op

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Missing operator permission"):
        svc.require_permission(_make_user(), OperatorPermission.MANAGE_OPERATORS)


def test_require_permission_raises_when_not_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    operator_repo.get_by_id.return_value = None

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Operator access required"):
        svc.require_permission(_make_user(), OperatorPermission.VIEW_METRICS)


# --- list_operators ---


def test_list_operators_returns_all_for_authorized_user() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    op = _make_operator(role=OperatorRole.ADMIN)
    operator_repo.get_by_id.return_value = op
    expected_list = [_make_operator(), _make_operator(pid=222222222)]
    operator_repo.list_all.return_value = expected_list

    svc = _build_service(operator_repo)
    result = svc.list_operators(_make_user())

    assert result is expected_list
    operator_repo.list_all.assert_called_once()


def test_list_operators_raises_for_helpdesk() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    op = _make_operator(role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.return_value = op

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Missing operator permission"):
        svc.list_operators(_make_user())


def test_list_operators_raises_for_non_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    operator_repo.get_by_id.return_value = None

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError):
        svc.list_operators(_make_user())


# --- grant_operator ---


def test_grant_operator_creates_record() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else None
    created = _make_operator(pid=222222222, role=OperatorRole.ADMIN)
    operator_repo.create.return_value = created

    svc = _build_service(operator_repo)
    caller = _make_user(pid=111111111)
    target = _make_user(pid=222222222)
    result = svc.grant_operator(caller, target, OperatorRole.ADMIN)

    assert result is created
    operator_repo.create.assert_called_once()


def test_grant_operator_raises_when_target_already_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    existing_op = _make_operator(pid=222222222, role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else existing_op

    svc = _build_service(operator_repo)

    with pytest.raises(ValueError, match="already an operator"):
        svc.grant_operator(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            OperatorRole.ADMIN,
        )


def test_grant_superadmin_requires_superadmin_caller() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.ADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else None

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="superadmin"):
        svc.grant_operator(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            OperatorRole.SUPERADMIN,
        )


def test_grant_operator_raises_for_non_operator_caller() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    operator_repo.get_by_id.return_value = None

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError):
        svc.grant_operator(
            _make_user(),
            _make_user(pid=222222222),
            OperatorRole.HELPDESK,
        )


# --- update_operator_role ---


def test_update_operator_role_changes_role() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    target_op = _make_operator(pid=222222222, role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else target_op
    operator_repo.update.return_value = target_op

    svc = _build_service(operator_repo)
    result = svc.update_operator_role(
        _make_user(pid=111111111),
        _make_user(pid=222222222),
        OperatorRole.ADMIN,
    )

    assert result is target_op
    operator_repo.update.assert_called_once_with(target_op)


def test_update_operator_role_raises_when_target_not_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else None

    svc = _build_service(operator_repo)

    with pytest.raises(ValueError, match="not an operator"):
        svc.update_operator_role(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            OperatorRole.ADMIN,
        )


def test_update_to_superadmin_requires_superadmin_caller() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.ADMIN)
    target_op = _make_operator(pid=222222222, role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else target_op

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="superadmin"):
        svc.update_operator_role(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            OperatorRole.SUPERADMIN,
        )


def test_update_superadmin_target_requires_superadmin_caller() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.ADMIN)
    target_op = _make_operator(pid=222222222, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else target_op

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="superadmin"):
        svc.update_operator_role(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            OperatorRole.ADMIN,
        )


# --- revoke_operator ---


def test_revoke_operator_removes_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    target_op = _make_operator(pid=222222222, role=OperatorRole.ADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else target_op

    svc = _build_service(operator_repo)
    svc.revoke_operator(_make_user(pid=111111111), _make_user(pid=222222222))

    operator_repo.delete.assert_called_once_with(target_op)


def test_revoke_operator_prevents_self_revocation() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.return_value = caller_op

    svc = _build_service(operator_repo)

    with pytest.raises(ValueError, match="Cannot revoke your own"):
        svc.revoke_operator(_make_user(pid=111111111), _make_user(pid=111111111))


def test_revoke_operator_raises_when_target_not_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else None

    svc = _build_service(operator_repo)

    with pytest.raises(ValueError, match="not an operator"):
        svc.revoke_operator(_make_user(pid=111111111), _make_user(pid=222222222))


def test_revoke_superadmin_requires_superadmin_caller() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.ADMIN)
    target_op = _make_operator(pid=222222222, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.side_effect = lambda pid: caller_op if pid == 111111111 else target_op

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="superadmin"):
        svc.revoke_operator(_make_user(pid=111111111), _make_user(pid=222222222))


def test_revoke_raises_for_helpdesk_caller() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.return_value = caller_op

    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Missing operator permission"):
        svc.revoke_operator(_make_user(pid=111111111), _make_user(pid=222222222))


# --- issue_impersonation_token ---


def test_issue_impersonation_token_returns_valid_jwt() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.SUPERADMIN)
    operator_repo.get_by_id.return_value = caller_op

    settings = _make_settings()
    svc = _build_service(operator_repo)

    subject = _make_user(pid=111111111)
    target = _make_user(pid=222222222)
    token = svc.issue_impersonation_token(subject, target, settings)

    decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
    assert decoded["sub"] == "222222222"
    assert decoded["impersonator"] == "111111111"
    assert "exp" in decoded


def test_issue_impersonation_token_raises_for_admin() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.ADMIN)
    operator_repo.get_by_id.return_value = caller_op

    settings = _make_settings()
    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Missing operator permission"):
        svc.issue_impersonation_token(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            settings,
        )


def test_issue_impersonation_token_raises_for_helpdesk() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    caller_op = _make_operator(pid=111111111, role=OperatorRole.HELPDESK)
    operator_repo.get_by_id.return_value = caller_op

    settings = _make_settings()
    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError, match="Missing operator permission"):
        svc.issue_impersonation_token(
            _make_user(pid=111111111),
            _make_user(pid=222222222),
            settings,
        )


def test_issue_impersonation_token_raises_for_non_operator() -> None:
    operator_repo = MagicMock(spec=OperatorRepository)
    operator_repo.get_by_id.return_value = None

    settings = _make_settings()
    svc = _build_service(operator_repo)

    with pytest.raises(AuthorizationError):
        svc.issue_impersonation_token(
            _make_user(),
            _make_user(pid=222222222),
            settings,
        )
