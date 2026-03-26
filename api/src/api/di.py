"""Dependency factories shared across FastAPI route handlers."""

from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, Path, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from learnwithai.config import Settings, get_settings
from learnwithai.db import get_session
from learnwithai.interfaces import JobQueue
from learnwithai.pagination import PaginationParams
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.repositories.course_repository import CourseRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.services.course_service import CourseService
from learnwithai.services.csxl_auth_service import (
    AuthenticationException,
    CSXLAuthService,
)
from learnwithai.services.roster_upload_service import RosterUploadService
from learnwithai.tables.course import Course
from learnwithai.tables.user import User
from learnwithai.tools.jokes import JokeGenerationService
from learnwithai_jobqueue.dramatiq_job_queue import DramatiqJobQueue
from sqlmodel import Session

__all__ = [
    "AsyncJobRepositoryDI",
    "AuthenticatedUserDI",
    "CSXLAuthServiceDI",
    "CourseByCourseIDPathDI",
    "CourseRepositoryDI",
    "CourseServiceDI",
    "JokeGenerationServiceDI",
    "JobQueueDI",
    "MembershipRepositoryDI",
    "PaginationParamsDI",
    "SessionDI",
    "SettingsDI",
    "UserByPIDPathDI",
    "UserRepositoryDI",
    "async_job_repository_factory",
    "course_repository_factory",
    "course_service_factory",
    "csxl_auth_service_factory",
    "get_authenticated_user",
    "get_course_by_path_id",
    "get_pagination_params",
    "get_user_by_path_pid",
    "get_user_by_pid",
    "joke_generation_service_factory",
    "job_queue_factory",
    "membership_repository_factory",
    "roster_upload_service_factory",
    "settings_factory",
    "user_repository_factory",
]


def csxl_auth_service_factory(settings: SettingsDI, user_repository: UserRepositoryDI) -> CSXLAuthService:
    """Creates the CSXL authentication service for the current request.

    Args:
        settings: Application settings.
        user_repository: Repository used to load and persist users.

    Returns:
        A configured CSXL authentication service.
    """
    return CSXLAuthService(settings, user_repository)


CSXLAuthServiceDI: TypeAlias = Annotated[CSXLAuthService, Depends(csxl_auth_service_factory)]


SessionDI: TypeAlias = Annotated[Session, Depends(get_session)]


def settings_factory() -> Settings:
    """Builds a settings object for FastAPI dependency injection."""
    return get_settings()


SettingsDI: TypeAlias = Annotated[Settings, Depends(settings_factory)]


def user_repository_factory(session: SessionDI) -> UserRepository:
    """Constructs a user repository bound to the current request session."""
    return UserRepository(session)


UserRepositoryDI: TypeAlias = Annotated[UserRepository, Depends(user_repository_factory)]


def course_repository_factory(session: SessionDI) -> CourseRepository:
    """Constructs a course repository bound to the current request session."""
    return CourseRepository(session)


CourseRepositoryDI: TypeAlias = Annotated[CourseRepository, Depends(course_repository_factory)]


def membership_repository_factory(session: SessionDI) -> MembershipRepository:
    """Constructs a membership repository bound to the current request session."""
    return MembershipRepository(session)


MembershipRepositoryDI: TypeAlias = Annotated[MembershipRepository, Depends(membership_repository_factory)]


def async_job_repository_factory(session: SessionDI) -> AsyncJobRepository:
    """Constructs an async job repository bound to the current request session."""
    return AsyncJobRepository(session)


AsyncJobRepositoryDI: TypeAlias = Annotated[AsyncJobRepository, Depends(async_job_repository_factory)]


def course_service_factory(
    course_repo: CourseRepositoryDI,
    membership_repo: MembershipRepositoryDI,
) -> CourseService:
    """Creates the course service for the current request."""
    return CourseService(course_repo, membership_repo)


CourseServiceDI: TypeAlias = Annotated[CourseService, Depends(course_service_factory)]


def get_authenticated_user(
    csxl_auth_svc: CSXLAuthServiceDI,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> User:
    """Authenticates the current request from a bearer token.

    The ``HTTPBearer`` security dependency extracts and validates the
    ``Authorization: Bearer <token>`` header automatically, returning
    a 403 when the header is absent or malformed.  This function then
    verifies the JWT and resolves the user.

    Args:
        csxl_auth_svc: Service used to validate and resolve subject identity.
        credentials: Bearer credentials extracted by FastAPI's HTTPBearer.

    Returns:
        The authenticated subject.

    Raises:
        HTTPException: If the token is invalid, expired, or the user is unknown.
    """
    try:
        pid = csxl_auth_svc.verify_jwt(credentials.credentials)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    subject = csxl_auth_svc.get_user_by_pid(pid)
    if subject is None:
        raise HTTPException(status_code=401, detail="User not found.")
    return subject


AuthenticatedUserDI: TypeAlias = Annotated[User, Depends(get_authenticated_user)]


def job_queue_factory() -> JobQueue:
    """Creates the job queue implementation used by API handlers."""
    return DramatiqJobQueue()


JobQueueDI: TypeAlias = Annotated[JobQueue, Depends(job_queue_factory)]


def get_course_by_path_id(course_id: Annotated[int, Path()], course_repo: CourseRepositoryDI) -> Course:
    """Loads a course from the course_id path parameter.

    Args:
        course_id: Course identifier from the request path.
        course_repo: Repository used to load courses.

    Returns:
        The matching course.

    Raises:
        HTTPException: If the course does not exist.
    """
    course = course_repo.get_by_id(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


CourseByCourseIDPathDI: TypeAlias = Annotated[Course, Depends(get_course_by_path_id)]


def get_user_by_pid(pid: int, user_repo: UserRepositoryDI) -> User:
    """Loads a user by pid or raises an HTTP 404.

    Args:
        pid: UNC person identifier.
        user_repo: Repository used to load users.

    Returns:
        The matching user.

    Raises:
        HTTPException: If the user does not exist.
    """
    user = user_repo.get_by_pid(pid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def get_user_by_path_pid(pid: Annotated[int, Path()], user_repo: UserRepositoryDI) -> User:
    """Loads a user from the pid path parameter.

    Args:
        pid: User identifier from the request path.
        user_repo: Repository used to load users.

    Returns:
        The matching user.
    """
    return get_user_by_pid(pid, user_repo)


UserByPIDPathDI: TypeAlias = Annotated[User, Depends(get_user_by_path_pid)]


def get_pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> PaginationParams:
    """Extracts pagination query parameters into a shared dataclass.

    Args:
        page: 1-based page number.
        page_size: Maximum items per page (1–100).

    Returns:
        A PaginationParams instance.
    """
    return PaginationParams(page=page, page_size=page_size)


PaginationParamsDI: TypeAlias = Annotated[PaginationParams, Depends(get_pagination_params)]


def roster_upload_service_factory(
    async_job_repo: AsyncJobRepositoryDI,
    user_repo: UserRepositoryDI,
    membership_repo: MembershipRepositoryDI,
    job_queue: JobQueueDI,
) -> RosterUploadService:
    """Creates the roster upload service for the current request."""
    return RosterUploadService(async_job_repo, user_repo, membership_repo, job_queue)


RosterUploadServiceDI: TypeAlias = Annotated[RosterUploadService, Depends(roster_upload_service_factory)]


def joke_generation_service_factory(
    async_job_repo: AsyncJobRepositoryDI,
    job_queue: JobQueueDI,
) -> JokeGenerationService:
    """Creates the joke generation service for the current request."""
    return JokeGenerationService(async_job_repo, job_queue)


JokeGenerationServiceDI: TypeAlias = Annotated[JokeGenerationService, Depends(joke_generation_service_factory)]
