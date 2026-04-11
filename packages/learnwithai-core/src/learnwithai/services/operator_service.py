# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Business logic for system operator management and authorization."""

from datetime import datetime, timedelta, timezone

import jwt

from ..config import Settings
from ..errors import AuthorizationError
from ..repositories.operator_repository import OperatorRepository
from ..repositories.user_repository import UserRepository
from ..tables.operator import (
    Operator,
    OperatorPermission,
    OperatorRole,
    effective_permissions,
)
from ..tables.user import User


class OperatorService:
    """Orchestrates operator CRUD and permission enforcement."""

    def __init__(
        self,
        operator_repo: OperatorRepository,
        user_repo: UserRepository,
    ):
        """Initializes the operator service.

        Args:
            operator_repo: Repository for operator persistence.
            user_repo: Repository for user lookups.
        """
        self._operator_repo = operator_repo
        self._user_repo = user_repo

    # -- Public API (literate style: big-picture first) --

    def get_operator(self, subject: User) -> Operator | None:
        """Returns the operator record for a user, or ``None``.

        Args:
            subject: User to look up.

        Returns:
            The operator record when the user is an operator; otherwise, ``None``.
        """
        return self._operator_repo.get_by_id(subject.pid)

    def require_operator(self, subject: User) -> Operator:
        """Verifies the subject is a system operator.

        Args:
            subject: Authenticated user.

        Returns:
            The operator record.

        Raises:
            AuthorizationError: If the subject is not an operator.
        """
        operator = self.get_operator(subject)
        if operator is None:
            raise AuthorizationError("Operator access required.")
        return operator

    def require_permission(
        self,
        subject: User,
        permission: OperatorPermission,
    ) -> Operator:
        """Verifies the subject holds a specific operator permission.

        Args:
            subject: Authenticated user.
            permission: The required permission.

        Returns:
            The operator record.

        Raises:
            AuthorizationError: If the subject lacks the permission.
        """
        operator = self.require_operator(subject)
        if permission not in effective_permissions(operator):
            raise AuthorizationError(f"Missing operator permission: {permission.value}")
        return operator

    def list_operators(self, subject: User) -> list[Operator]:
        """Returns all operator records.

        Requires ``MANAGE_OPERATORS`` permission.

        Args:
            subject: Authenticated user requesting the list.

        Returns:
            All operator records with user data eagerly loaded.

        Raises:
            AuthorizationError: If the subject lacks permission.
        """
        self.require_permission(subject, OperatorPermission.MANAGE_OPERATORS)
        return self._operator_repo.list_all()

    def grant_operator(
        self,
        subject: User,
        target_user: User,
        role: OperatorRole,
    ) -> Operator:
        """Grants operator access to a user.

        Requires ``MANAGE_OPERATORS`` permission. Only a ``SUPERADMIN``
        may grant the ``SUPERADMIN`` role.

        Args:
            subject: Authenticated operator performing the grant.
            target_user: User receiving operator access.
            role: Role to assign.

        Returns:
            The newly created operator record.

        Raises:
            AuthorizationError: If the subject lacks permission or attempts
                an unauthorized role assignment.
            ValueError: If the target user is already an operator.
        """
        operator = self.require_permission(subject, OperatorPermission.MANAGE_OPERATORS)
        self._require_superadmin_for_superadmin_role(operator, role)

        existing = self._operator_repo.get_by_id(target_user.pid)
        if existing is not None:
            raise ValueError("User is already an operator.")

        return self._operator_repo.create(
            Operator(
                user_pid=target_user.pid,
                role=role,
                created_by_pid=subject.pid,
            )
        )

    def update_operator_role(
        self,
        subject: User,
        target_user: User,
        role: OperatorRole,
    ) -> Operator:
        """Changes the role of an existing operator.

        Requires ``MANAGE_OPERATORS`` permission. Only a ``SUPERADMIN``
        may assign the ``SUPERADMIN`` role.

        Args:
            subject: Authenticated operator performing the update.
            target_user: Operator whose role should change.
            role: New role to assign.

        Returns:
            The updated operator record.

        Raises:
            AuthorizationError: If the subject lacks permission.
            ValueError: If the target user is not an operator.
        """
        caller = self.require_permission(subject, OperatorPermission.MANAGE_OPERATORS)
        self._require_superadmin_for_superadmin_role(caller, role)

        target_op = self._operator_repo.get_by_id(target_user.pid)
        if target_op is None:
            raise ValueError("Target user is not an operator.")

        self._require_superadmin_for_superadmin_role(caller, target_op.role)

        target_op.role = role
        return self._operator_repo.update(target_op)

    def revoke_operator(self, subject: User, target_user: User) -> None:
        """Removes operator access from a user.

        Requires ``MANAGE_OPERATORS`` permission. An operator cannot
        revoke their own access. Only a ``SUPERADMIN`` may revoke
        another ``SUPERADMIN``.

        Args:
            subject: Authenticated operator performing the revocation.
            target_user: Operator whose access should be removed.

        Raises:
            AuthorizationError: If the subject lacks permission or
                attempts a disallowed revocation.
            ValueError: If the target user is not an operator or the
                subject attempts self-revocation.
        """
        caller = self.require_permission(subject, OperatorPermission.MANAGE_OPERATORS)

        if subject.pid == target_user.pid:
            raise ValueError("Cannot revoke your own operator access.")

        target_op = self._operator_repo.get_by_id(target_user.pid)
        if target_op is None:
            raise ValueError("Target user is not an operator.")

        self._require_superadmin_for_superadmin_role(caller, target_op.role)

        self._operator_repo.delete(target_op)

    def issue_impersonation_token(
        self,
        subject: User,
        target_user: User,
        settings: Settings,
    ) -> str:
        """Issues a JWT that authenticates as the target user.

        The token carries an ``impersonator`` claim recording the
        operator's PID for audit purposes. Existing JWT verification
        ignores this extra claim, so no changes to the auth pipeline
        are required.

        Requires ``IMPERSONATE`` permission.

        Args:
            subject: Operator requesting impersonation.
            target_user: User to impersonate.
            settings: Application settings for JWT encoding.

        Returns:
            Encoded JWT string.

        Raises:
            AuthorizationError: If the subject lacks permission.
        """
        self.require_permission(subject, OperatorPermission.IMPERSONATE)

        expire_at = datetime.now(timezone.utc) + timedelta(days=1)
        payload = {
            "sub": str(target_user.pid),
            "exp": expire_at,
            "impersonator": str(subject.pid),
        }
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

    # -- Private helpers (details last) --

    def _require_superadmin_for_superadmin_role(
        self,
        caller: Operator,
        role: OperatorRole,
    ) -> None:
        """Guards SUPERADMIN role assignment to SUPERADMIN callers only.

        Args:
            caller: The operator performing the action.
            role: The role being assigned or affected.

        Raises:
            AuthorizationError: If a non-SUPERADMIN attempts to manage the
                SUPERADMIN role.
        """
        if role == OperatorRole.SUPERADMIN and caller.role != OperatorRole.SUPERADMIN:
            raise AuthorizationError("Only a superadmin may manage the superadmin role.")
