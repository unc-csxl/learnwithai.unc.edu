"""Development-only routes for local testing and database management.

These routes are only registered when the application is running in the
``development`` environment. They are never available in production.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from learnwithai.db import get_engine, reset_db_and_tables
from learnwithai.dev_data import seed
from sqlmodel import Session

from ..di import CSXLAuthServiceDI, UserRepositoryDI
from ..models.user_profile import UserProfile

router = APIRouter(tags=["Development"])


@router.get(
    "/dev/users",
    summary="List all registered users (dev only)",
    response_description="List of all registered users.",
)
def dev_list_users(user_repo: UserRepositoryDI) -> list[UserProfile]:
    """Returns all registered users for the development login chooser.

    Args:
        user_repo: Repository used to load users.

    Returns:
        A list of all registered user profiles.
    """
    users = user_repo.list_all()
    return [UserProfile.model_validate(u) for u in users]


@router.get(
    "/auth/as/{pid}",
    summary="Log in as a user by PID (dev only)",
    response_description="Redirect to the frontend with a local JWT.",
    responses={
        302: {"description": "Redirect to the frontend with a JWT."},
        404: {"description": "No user with the given PID exists."},
    },
)
def dev_login_as(pid: int, csxl_auth_svc: CSXLAuthServiceDI) -> RedirectResponse:
    """Issues a JWT for the user identified by *pid* and redirects to the frontend.

    This bypasses external UNC authentication entirely. The user must already
    exist in the local database.

    Args:
        pid: UNC person identifier of the user to authenticate as.
        csxl_auth_svc: Service used to look up the user and issue a JWT.

    Returns:
        A redirect to ``/jwt?token=<jwt>`` when the user exists.

    Raises:
        HTTPException: 404 when no user with the given PID is found.
    """
    user = csxl_auth_svc.get_user_by_pid(pid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    jwt: str = csxl_auth_svc.issue_jwt_token(user)
    return RedirectResponse(url=f"/jwt?token={jwt}", status_code=302)


@router.post(
    "/dev/reset-db",
    summary="Reset and seed the development database",
    response_description="Confirmation that the database was reset.",
)
def dev_reset_db() -> dict[str, str]:
    """Drops and recreates the database, then inserts development seed data.

    Returns:
        A simple status message confirming the reset.
    """
    reset_db_and_tables()
    with Session(get_engine()) as session:
        seed(session)
        session.commit()
    return {"detail": "Database reset and seeded."}
