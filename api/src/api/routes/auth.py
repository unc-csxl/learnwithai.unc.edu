from typing import Annotated
from fastapi import APIRouter, Response, Query, HTTPException
from fastapi.responses import RedirectResponse
from ..dependency_injection import CSXLAuthServiceDI, SettingsDI, SessionDI, CurrentUserDI
from learnwithai.services.csxl_auth_service import AuthenticationException

router = APIRouter()


@router.get("/onyen")
def onyen_login_redirect(settings: SettingsDI) -> Response:
    origin = f"{settings.host}/auth"
    continue_to = ""
    return RedirectResponse(
        url=f"https://{settings.unc_auth_server_host}/auth?origin={origin}&continue_to={continue_to}",
        status_code=307,
    )


@router.get("/me")
def get_current_user_profile(user: CurrentUserDI) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "pid": user.pid,
        "onyen": user.onyen,
        "email": user.email,
    }


@router.get("")
def authenticate_with_csxl_callback(
    session: SessionDI,
    csxl_auth_svc: CSXLAuthServiceDI,
    token: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    if token is None:
        return RedirectResponse(url="/", status_code=302)

    # Verify token's contents with XL
    try:
        onyen, pid = csxl_auth_svc.verify_auth_token(token)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="You are not authenticated.")

    # Register new or retrieve existing user by their ONYEN and PID.
    try:
        with session.begin():
            user = csxl_auth_svc.registered_user_from_onyen_pid(onyen, pid)
    except AuthenticationException:
        raise HTTPException(status_code=500, detail="Failed to register user.")

    # Issue a token to the client to authenticate with our service
    jwt: str = csxl_auth_svc.issue_jwt_token(user)
    return RedirectResponse(url=f"/jwt?token={jwt}", status_code=302)
