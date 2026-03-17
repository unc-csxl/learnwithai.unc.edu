"""Dependency factories shared across FastAPI route handlers."""

from typing import TypeAlias, Annotated
from fastapi import Depends, Header, HTTPException
from learnwithai.config import Settings
from learnwithai.services.csxl_auth_service import (
    CSXLAuthService,
    AuthenticationException,
)
from learnwithai.db import get_session, Session
from learnwithai.interfaces import JobQueue
from learnwithai.tables.user import User
from learnwithai.repositories.user_repository import UserRepository
from learnwithai_jobqueue.dramatiq_job_queue import DramatiqJobQueue

SessionDI: TypeAlias = Annotated[Session, Depends(get_session)]


def settings_factory() -> Settings:
    """Builds a settings object for FastAPI dependency injection."""
    return Settings()


SettingsDI: TypeAlias = Annotated[Settings, Depends(settings_factory)]


def user_repository_factory(session: SessionDI) -> UserRepository:
    """Constructs a user repository bound to the current request session.

    Args:
        session: Database session scoped to the request.

    Returns:
        A repository backed by the provided database session.
    """
    return UserRepository(session)


UserRepositoryDI: TypeAlias = Annotated[
    UserRepository, Depends(user_repository_factory)
]


def csxl_auth_service_factory(
    settings: SettingsDI, user_repository: UserRepositoryDI
) -> CSXLAuthService:
    """Creates the CSXL authentication service for the current request.

    Args:
        settings: Application settings.
        user_repository: Repository used to load and persist users.

    Returns:
        A configured CSXL authentication service.
    """
    return CSXLAuthService(settings, user_repository)


CSXLAuthServiceDI: TypeAlias = Annotated[
    CSXLAuthService, Depends(csxl_auth_service_factory)
]


def get_current_user(
    csxl_auth_svc: CSXLAuthServiceDI,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Authenticates the current request from a bearer token.

    Args:
        csxl_auth_svc: Service used to validate and resolve user identity.
        authorization: Raw Authorization header supplied by the client.

    Returns:
        The authenticated user.

    Raises:
        HTTPException: If the token is missing, invalid, expired, or unknown.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")
    token = authorization.removeprefix("Bearer ")
    try:
        user_id = csxl_auth_svc.verify_jwt(token)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = csxl_auth_svc.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


CurrentUserDI: TypeAlias = Annotated[User, Depends(get_current_user)]


def job_queue_factory() -> JobQueue:
    """Creates the job queue implementation used by API handlers."""
    return DramatiqJobQueue()


JobQueueDI: TypeAlias = Annotated[JobQueue, Depends(job_queue_factory)]
