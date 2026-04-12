# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for operator table definitions and permission resolution."""

from __future__ import annotations

from unittest.mock import MagicMock

from learnwithai.tables.operator import (
    ROLE_PERMISSIONS,
    Operator,
    OperatorPermission,
    OperatorRole,
    effective_permissions,
)

# --- OperatorRole ---


def test_operator_role_values() -> None:
    assert OperatorRole.SUPERADMIN.value == "superadmin"
    assert OperatorRole.ADMIN.value == "admin"
    assert OperatorRole.HELPDESK.value == "helpdesk"


def test_operator_role_has_three_members() -> None:
    assert len(OperatorRole) == 3


# --- OperatorPermission ---


def test_operator_permission_values() -> None:
    assert OperatorPermission.MANAGE_OPERATORS.value == "manage_operators"
    assert OperatorPermission.VIEW_METRICS.value == "view_metrics"
    assert OperatorPermission.VIEW_JOBS.value == "view_jobs"
    assert OperatorPermission.VIEW_SYSTEM.value == "view_system"
    assert OperatorPermission.IMPERSONATE.value == "impersonate"


def test_operator_permission_has_five_members() -> None:
    assert len(OperatorPermission) == 5


# --- ROLE_PERMISSIONS mapping ---


def test_superadmin_has_all_permissions() -> None:
    assert ROLE_PERMISSIONS[OperatorRole.SUPERADMIN] == frozenset(OperatorPermission)


def test_admin_permissions() -> None:
    expected = frozenset(
        {
            OperatorPermission.MANAGE_OPERATORS,
            OperatorPermission.VIEW_METRICS,
            OperatorPermission.VIEW_JOBS,
            OperatorPermission.VIEW_SYSTEM,
        }
    )
    assert ROLE_PERMISSIONS[OperatorRole.ADMIN] == expected


def test_admin_cannot_impersonate() -> None:
    assert OperatorPermission.IMPERSONATE not in ROLE_PERMISSIONS[OperatorRole.ADMIN]


def test_helpdesk_permissions() -> None:
    expected = frozenset(
        {
            OperatorPermission.VIEW_METRICS,
            OperatorPermission.VIEW_JOBS,
        }
    )
    assert ROLE_PERMISSIONS[OperatorRole.HELPDESK] == expected


def test_helpdesk_cannot_manage_operators() -> None:
    assert OperatorPermission.MANAGE_OPERATORS not in ROLE_PERMISSIONS[OperatorRole.HELPDESK]


def test_helpdesk_cannot_impersonate() -> None:
    assert OperatorPermission.IMPERSONATE not in ROLE_PERMISSIONS[OperatorRole.HELPDESK]


def test_every_role_has_a_mapping() -> None:
    for role in OperatorRole:
        assert role in ROLE_PERMISSIONS


# --- effective_permissions ---


def _make_operator(role: OperatorRole) -> MagicMock:
    m = MagicMock(spec=Operator)
    m.role = role
    return m


def test_effective_permissions_superadmin() -> None:
    op = _make_operator(OperatorRole.SUPERADMIN)
    assert effective_permissions(op) == frozenset(OperatorPermission)


def test_effective_permissions_admin() -> None:
    op = _make_operator(OperatorRole.ADMIN)
    perms = effective_permissions(op)
    assert OperatorPermission.MANAGE_OPERATORS in perms
    assert OperatorPermission.IMPERSONATE not in perms


def test_effective_permissions_helpdesk() -> None:
    op = _make_operator(OperatorRole.HELPDESK)
    perms = effective_permissions(op)
    assert OperatorPermission.VIEW_METRICS in perms
    assert OperatorPermission.VIEW_JOBS in perms
    assert OperatorPermission.MANAGE_OPERATORS not in perms
    assert OperatorPermission.IMPERSONATE not in perms
