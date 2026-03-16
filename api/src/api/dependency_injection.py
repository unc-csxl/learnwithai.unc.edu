from typing import TypeAlias, Annotated
from fastapi import Depends
from learnwithai.config import Settings
from learnwithai.services.csxl_auth_service import CSXLAuthService
from learnwithai.db import get_session, Session
from learnwithai.interfaces import JobQueue
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


def job_queue_factory() -> JobQueue:
    return DramatiqJobQueue()


JobQueueDI: TypeAlias = Annotated[JobQueue, Depends(job_queue_factory)]
