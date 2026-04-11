# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Operations routes for system operator management and impersonation."""

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query
from learnwithai.tables.operator import effective_permissions

from ..di import (
    AuthenticatedUserDI,
    MetricsServiceDI,
    OperatorServiceDI,
    SettingsDI,
    UserRepositoryDI,
)
from ..models import (
    GrantOperatorRequest,
    ImpersonationTokenResponse,
    OperatorResponse,
    UpdateOperatorRoleRequest,
    UsageMetricsResponse,
    UserSearchResult,
)

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get(
    "/metrics",
    response_model=UsageMetricsResponse,
    summary="Get platform usage metrics",
    response_description="Monthly usage statistics.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires VIEW_METRICS permission."},
    },
)
def get_usage_metrics(
    subject: AuthenticatedUserDI,
    metrics_svc: MetricsServiceDI,
) -> UsageMetricsResponse:
    """Returns monthly usage metrics for the platform.

    Requires VIEW_METRICS permission.

    Args:
        subject: Authenticated operator.
        metrics_svc: Service for computing usage metrics.

    Returns:
        Monthly usage statistics.
    """
    metrics = metrics_svc.get_usage_metrics(subject)
    return UsageMetricsResponse(
        month_label=metrics.month_label,
        active_users=metrics.active_users,
        active_courses=metrics.active_courses,
        submissions=metrics.submissions,
        jobs_run=metrics.jobs_run,
    )


def _build_operator_response(operator) -> OperatorResponse:  # noqa: ANN001
    """Converts an Operator domain object to an OperatorResponse model.

    Args:
        operator: Operator record with eagerly loaded user.

    Returns:
        An OperatorResponse for the API.
    """
    return OperatorResponse(
        user_pid=operator.user_pid,
        user_name=operator.user.name,
        user_email=operator.user.email,
        role=operator.role,
        permissions=sorted(effective_permissions(operator), key=lambda p: p.value),
        created_at=operator.created_at,
        created_by_pid=operator.created_by_pid,
    )


@router.get(
    "/operators",
    response_model=list[OperatorResponse],
    summary="List all operators",
    response_description="All system operators with user details.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires MANAGE_OPERATORS permission."},
    },
)
def list_operators(
    subject: AuthenticatedUserDI,
    operator_svc: OperatorServiceDI,
) -> list[OperatorResponse]:
    """Returns all operator records.

    Requires MANAGE_OPERATORS permission.

    Args:
        subject: Authenticated operator.
        operator_svc: Service used to enforce permissions and list operators.

    Returns:
        List of all operator records.
    """
    operators = operator_svc.list_operators(subject)
    return [_build_operator_response(op) for op in operators]


@router.post(
    "/operators",
    response_model=OperatorResponse,
    status_code=201,
    summary="Grant operator access",
    response_description="The newly created operator record.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires MANAGE_OPERATORS permission."},
        404: {"description": "User not found."},
        409: {"description": "User is already an operator."},
    },
)
def grant_operator(
    subject: AuthenticatedUserDI,
    body: Annotated[GrantOperatorRequest, Body()],
    operator_svc: OperatorServiceDI,
    user_repo: UserRepositoryDI,
) -> OperatorResponse:
    """Grants operator access to an existing user.

    Requires MANAGE_OPERATORS permission. Only a SUPERADMIN may grant
    the SUPERADMIN role.

    Args:
        subject: Authenticated operator performing the grant.
        body: Grant request payload with user PID and role.
        operator_svc: Service used to enforce permissions and create operator.
        user_repo: Repository used to load the target user.

    Returns:
        The newly created operator record.
    """
    target_user = user_repo.get_by_pid(body.user_pid)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        operator = operator_svc.grant_operator(subject, target_user, body.role)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Reload with user relationship for response
    operator.user = target_user
    return _build_operator_response(operator)


@router.put(
    "/operators/{pid}",
    response_model=OperatorResponse,
    summary="Update an operator's role",
    response_description="The updated operator record.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires MANAGE_OPERATORS permission."},
        404: {"description": "User or operator not found."},
    },
)
def update_operator_role(
    subject: AuthenticatedUserDI,
    pid: int,
    body: Annotated[UpdateOperatorRoleRequest, Body()],
    operator_svc: OperatorServiceDI,
    user_repo: UserRepositoryDI,
) -> OperatorResponse:
    """Changes the role of an existing operator.

    Requires MANAGE_OPERATORS permission. Only a SUPERADMIN may assign
    the SUPERADMIN role.

    Args:
        subject: Authenticated operator performing the update.
        pid: PID of the operator to update (path parameter).
        body: Update request payload with new role.
        operator_svc: Service used to enforce permissions and update role.
        user_repo: Repository used to load the target user.

    Returns:
        The updated operator record.
    """
    target_user = user_repo.get_by_pid(pid)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        operator = operator_svc.update_operator_role(subject, target_user, body.role)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    operator.user = target_user
    return _build_operator_response(operator)


@router.delete(
    "/operators/{pid}",
    status_code=204,
    summary="Revoke operator access",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires MANAGE_OPERATORS permission."},
        404: {"description": "User or operator not found."},
        409: {"description": "Cannot revoke own access."},
    },
)
def revoke_operator(
    subject: AuthenticatedUserDI,
    pid: int,
    operator_svc: OperatorServiceDI,
    user_repo: UserRepositoryDI,
) -> None:
    """Removes operator access from a user.

    Requires MANAGE_OPERATORS permission. Cannot revoke own access.
    Only a SUPERADMIN may revoke another SUPERADMIN.

    Args:
        subject: Authenticated operator performing the revocation.
        pid: PID of the operator to revoke (path parameter).
        operator_svc: Service used to enforce permissions and revoke access.
        user_repo: Repository used to load the target user.
    """
    target_user = user_repo.get_by_pid(pid)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        operator_svc.revoke_operator(subject, target_user)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/impersonate/{pid}",
    response_model=ImpersonationTokenResponse,
    summary="Issue an impersonation token",
    response_description="JWT token for impersonating the target user.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires IMPERSONATE permission."},
        404: {"description": "User not found."},
    },
)
def impersonate_user(
    subject: AuthenticatedUserDI,
    pid: int,
    operator_svc: OperatorServiceDI,
    user_repo: UserRepositoryDI,
    settings: SettingsDI,
) -> ImpersonationTokenResponse:
    """Issues a JWT that authenticates as the target user.

    Requires IMPERSONATE permission (currently only SUPERADMIN).
    The issued token carries an ``impersonator`` claim for audit purposes.

    Args:
        subject: Authenticated operator requesting impersonation.
        pid: PID of the user to impersonate (path parameter).
        operator_svc: Service used to enforce permissions and issue token.
        user_repo: Repository used to load the target user.
        settings: Application settings for JWT encoding.

    Returns:
        An ImpersonationTokenResponse containing the JWT.
    """
    target_user = user_repo.get_by_pid(pid)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    token = operator_svc.issue_impersonation_token(subject, target_user, settings)
    return ImpersonationTokenResponse(token=token)


@router.get(
    "/users/search",
    response_model=list[UserSearchResult],
    summary="Search users by name, PID, or email",
    response_description="Users matching the search query.",
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Requires IMPERSONATE permission."},
    },
)
def search_users(
    subject: AuthenticatedUserDI,
    q: Annotated[str, Query(min_length=1)],
    operator_svc: OperatorServiceDI,
    user_repo: UserRepositoryDI,
) -> list[UserSearchResult]:
    """Searches for users by name, PID, or email.

    Requires IMPERSONATE permission. Returns at most 20 results.

    Args:
        subject: Authenticated operator.
        q: Search query string.
        operator_svc: Service used to enforce permissions.
        user_repo: Repository used to search users.

    Returns:
        List of matching users.
    """
    from learnwithai.tables.operator import OperatorPermission

    operator_svc.require_permission(subject, OperatorPermission.IMPERSONATE)
    users = user_repo.search_users(q)
    return [UserSearchResult.model_validate(u, from_attributes=True) for u in users]
