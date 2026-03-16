from typing import TypeAlias, Annotated
from fastapi import Depends, Header, HTTPException
from learnwithai.config import Settings
from learnwithai.services.csxl_auth_service import (
    CSXLAuthService,
    AuthenticationException,
)
from learnwithai.db import get_session, Session
from learnwithai.interfaces import JobQueue
from learnwithai.models.user import User
from learnwithai.repositories.user_repository import UserRepository
from learnwithai_jobqueue.dramatiq_job_queue import DramatiqJobQueue

SessionDI: TypeAlias = Annotated[Session, Depends(get_session)]


def settings_factory() -> Settings:
    return Settings()


SettingsDI: TypeAlias = Annotated[Settings, Depends(settings_factory)]


def user_repository_factory(session: SessionDI) -> UserRepository:
    return UserRepository(session)


UserRepositoryDI: TypeAlias = Annotated[
    UserRepository, Depends(user_repository_factory)
]


def csxl_auth_service_factory(
    settings: SettingsDI, user_repository: UserRepositoryDI
) -> CSXLAuthService:
    return CSXLAuthService(settings, user_repository)


CSXLAuthServiceDI: TypeAlias = Annotated[
    CSXLAuthService, Depends(csxl_auth_service_factory)
]


def get_current_user(
    csxl_auth_svc: CSXLAuthServiceDI,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
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
    return DramatiqJobQueue()


JobQueueDI: TypeAlias = Annotated[JobQueue, Depends(job_queue_factory)]
