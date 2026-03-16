import httpx
from typing import Annotated
from fastapi import APIRouter, Response, Query, HTTPException
from fastapi.responses import RedirectResponse
from ..config import SettingsDI, Settings

router = APIRouter()


@router.get("/onyen")
def health(settings: SettingsDI) -> Response:
    continue_to = ""
    return RedirectResponse(
        url=f"https://{settings.unc_auth_server_host}/auth?origin={settings.host}/auth&continue_to={continue_to}",
        status_code=307,
    )

@router.get("")
def authenticate_with_csxl_callback(
    settings: SettingsDI,
    token: Annotated[str | None, Query()] = None,
):
    if token is None:
        return RedirectResponse(url="/", status_code=302)

    _onyen, pid = _verify_delegated_auth_token(settings, token)

    return pid


def _verify_delegated_auth_token(settings: Settings, token: str):
    params = {"token": token}

    with httpx.Client() as client:
        response = client.get(
            f"https://{settings.unc_auth_server_host}/verify", params=params
        )
        if response.status_code == httpx.codes.OK:
            body = response.json()
            onyen = body["uid"]
            pid = body["pid"]
            return (onyen, pid)
        else:
            raise HTTPException(status_code=401, detail="You are not authenticated.")