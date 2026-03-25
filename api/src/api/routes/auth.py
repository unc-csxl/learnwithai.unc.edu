"""Authentication routes for the public API."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from ..di import (
    CSXLAuthServiceDI,
    SettingsDI,
)
from learnwithai.services.csxl_auth_service import AuthenticationException

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/onyen",
    summary="Start UNC authentication",
    status_code=307,
    response_description="Redirect to the upstream UNC authentication flow.",
    responses={307: {"description": "Temporary redirect to UNC authentication."}},
)
def onyen_login_redirect(settings: SettingsDI) -> Response:
    """Redirects the client to the UNC authentication flow.

    Args:
        settings: Application settings used to build the callback URL.

    Returns:
        A redirect response to the upstream authentication service.
    """
    origin = f"{settings.host}/api/auth"
    continue_to = ""
    return RedirectResponse(
        url=f"https://{settings.unc_auth_server_host}/auth?origin={origin}&continue_to={continue_to}",
        status_code=307,
    )


@router.get(
    "",
    summary="Complete UNC authentication callback",
    response_description="Redirect to the frontend after authentication completes.",
    responses={
        302: {"description": "Redirect to the frontend after authentication."},
        401: {"description": "The provided upstream authentication token is invalid."},
        500: {"description": "The user could not be registered locally."},
    },
)
def authenticate_with_csxl_callback(
    csxl_auth_svc: CSXLAuthServiceDI,
    token: Annotated[
        str | None,
        Query(description="Token returned by the upstream CSXL authentication flow."),
    ] = None,
) -> RedirectResponse:
    """Completes the CSXL callback flow and issues a local JWT.

    Args:
        csxl_auth_svc: Service used to validate CSXL tokens and manage users.
        token: Token returned by the upstream CSXL authentication flow.

    Returns:
        A redirect to the frontend with a local JWT when authentication succeeds.

    Raises:
        HTTPException: If authentication fails or user registration cannot complete.
    """
    if token is None:
        return RedirectResponse(url="/", status_code=302)

    # Verify token's contents with XL
    try:
        onyen, pid = csxl_auth_svc.verify_auth_token(token)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="You are not authenticated.")

    # Register new or retrieve existing user by their ONYEN and PID.
    try:
        user = csxl_auth_svc.registered_user_from_onyen_pid(onyen, pid)
    except AuthenticationException:
        raise HTTPException(status_code=500, detail="Failed to register user.")

    # Issue a token to the client to authenticate with our service
    jwt: str = csxl_auth_svc.issue_jwt_token(user)
    return RedirectResponse(url=f"/jwt?token={jwt}", status_code=302)
