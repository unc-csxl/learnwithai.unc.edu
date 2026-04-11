# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Dependency factories shared across FastAPI route handlers."""

from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, Path, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from learnwithai.activities.iyow.repository import IyowActivityRepository, IyowSubmissionRepository
from learnwithai.activities.iyow.service import IyowActivityService
from learnwithai.activities.iyow.submission_service import IyowSubmissionService
from learnwithai.config import Settings, get_settings
from learnwithai.db import get_session
from learnwithai.interfaces import JobQueue
from learnwithai.pagination import PaginationParams
from learnwithai.rabbitmq_management import RabbitMQManagementClient
from learnwithai.repositories.activity_repository import ActivityRepository
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.repositories.course_repository import CourseRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.repositories.operator_repository import OperatorRepository
from learnwithai.repositories.submission_repository import SubmissionRepository
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.services.activity_service import ActivityService
from learnwithai.services.course_service import CourseService
from learnwithai.services.csxl_auth_service import (
    AuthenticationException,
    CSXLAuthService,
)
from learnwithai.services.job_control_service import JobControlService
from learnwithai.services.metrics_service import MetricsService
from learnwithai.services.operator_service import OperatorService
from learnwithai.services.roster_upload_service import RosterUploadService
from learnwithai.tables.activity import Activity
from learnwithai.tables.course import Course
from learnwithai.tables.user import User
from learnwithai.tools.jokes.repository import JokeRepository
from learnwithai.tools.jokes.service import JokeGenerationService
from learnwithai_jobqueue.dramatiq_job_queue import DramatiqJobQueue
from sqlmodel import Session

__all__ = [
    "ActivityByPathDI",
    "ActivityRepositoryDI",
    "ActivityServiceDI",
    "AsyncJobRepositoryDI",
    "AuthenticatedUserDI",
    "CSXLAuthServiceDI",
    "CourseByCourseIDPathDI",
    "CourseRepositoryDI",
    "CourseServiceDI",
    "IyowActivityRepositoryDI",
    "IyowActivityServiceDI",
    "IyowSubmissionRepositoryDI",
    "IyowSubmissionServiceDI",
    "JokeGenerationServiceDI",
    "JokeRepositoryDI",
    "JobControlServiceDI",
    "JobQueueDI",
    "MembershipRepositoryDI",
    "MetricsServiceDI",
    "OperatorRepositoryDI",
    "OperatorServiceDI",
    "PaginationParamsDI",
    "SessionDI",
    "SettingsDI",
    "SubmissionRepositoryDI",
    "UserByPIDPathDI",
    "UserRepositoryDI",
    "activity_repository_factory",
    "activity_service_factory",
    "async_job_repository_factory",
    "course_repository_factory",
    "course_service_factory",
    "csxl_auth_service_factory",
    "get_activity_by_path_id",
    "get_authenticated_user",
    "get_course_by_path_id",
    "get_pagination_params",
    "get_user_by_path_pid",
    "get_user_by_pid",
    "iyow_activity_repository_factory",
    "iyow_activity_service_factory",
    "iyow_submission_repository_factory",
    "iyow_submission_service_factory",
    "job_control_service_factory",
    "joke_generation_service_factory",
    "joke_repository_factory",
    "job_queue_factory",
    "membership_repository_factory",
    "metrics_service_factory",
    "operator_repository_factory",
    "operator_service_factory",
    "roster_upload_service_factory",
    "settings_factory",
    "submission_repository_factory",
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


def joke_repository_factory(session: SessionDI) -> JokeRepository:
    """Constructs a joke repository bound to the current request session."""
    return JokeRepository(session)


JokeRepositoryDI: TypeAlias = Annotated[JokeRepository, Depends(joke_repository_factory)]


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


def job_queue_factory(session: SessionDI) -> JobQueue:
    """Creates the request-scoped job queue used by API handlers."""
    return DramatiqJobQueue(session=session)


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


# ---- Operator DI ----


def operator_repository_factory(session: SessionDI) -> OperatorRepository:
    """Constructs an operator repository bound to the current request session."""
    return OperatorRepository(session)


OperatorRepositoryDI: TypeAlias = Annotated[OperatorRepository, Depends(operator_repository_factory)]


def operator_service_factory(
    operator_repo: OperatorRepositoryDI,
    user_repo: UserRepositoryDI,
) -> OperatorService:
    """Creates the operator service for the current request."""
    return OperatorService(operator_repo, user_repo)


OperatorServiceDI: TypeAlias = Annotated[OperatorService, Depends(operator_service_factory)]


def metrics_service_factory(
    session: SessionDI,
    operator_svc: OperatorServiceDI,
) -> MetricsService:
    """Creates the metrics service for the current request."""
    return MetricsService(session, operator_svc)


MetricsServiceDI: TypeAlias = Annotated[MetricsService, Depends(metrics_service_factory)]


def job_control_service_factory(
    session: SessionDI,
    operator_svc: OperatorServiceDI,
    settings: SettingsDI,
) -> JobControlService:
    """Creates the job control service for the current request."""
    client = RabbitMQManagementClient(
        base_url=settings.effective_rabbitmq_management_url,
        username=settings.rabbitmq_management_user,
        password=settings.rabbitmq_management_password,
    )
    return JobControlService(session, operator_svc, client)


JobControlServiceDI: TypeAlias = Annotated[JobControlService, Depends(job_control_service_factory)]


def joke_generation_service_factory(
    joke_repo: JokeRepositoryDI,
    async_job_repo: AsyncJobRepositoryDI,
    job_queue: JobQueueDI,
) -> JokeGenerationService:
    """Creates the joke generation service for the current request."""
    return JokeGenerationService(joke_repo, async_job_repo, job_queue)


JokeGenerationServiceDI: TypeAlias = Annotated[JokeGenerationService, Depends(joke_generation_service_factory)]


# ---- Activity / IYOW DI ----


def activity_repository_factory(session: SessionDI) -> ActivityRepository:
    """Constructs an activity repository bound to the current request session."""
    return ActivityRepository(session)


ActivityRepositoryDI: TypeAlias = Annotated[ActivityRepository, Depends(activity_repository_factory)]


def submission_repository_factory(session: SessionDI) -> SubmissionRepository:
    """Constructs a submission repository bound to the current request session."""
    return SubmissionRepository(session)


SubmissionRepositoryDI: TypeAlias = Annotated[SubmissionRepository, Depends(submission_repository_factory)]


def iyow_activity_repository_factory(session: SessionDI) -> IyowActivityRepository:
    """Constructs an IYOW activity repository bound to the current request session."""
    return IyowActivityRepository(session)


IyowActivityRepositoryDI: TypeAlias = Annotated[IyowActivityRepository, Depends(iyow_activity_repository_factory)]


def iyow_submission_repository_factory(session: SessionDI) -> IyowSubmissionRepository:
    """Constructs an IYOW submission repository bound to the current request session."""
    return IyowSubmissionRepository(session)


IyowSubmissionRepositoryDI: TypeAlias = Annotated[IyowSubmissionRepository, Depends(iyow_submission_repository_factory)]


def activity_service_factory(
    activity_repo: ActivityRepositoryDI,
    membership_repo: MembershipRepositoryDI,
) -> ActivityService:
    """Creates the activity service for the current request."""
    return ActivityService(activity_repo, membership_repo)


ActivityServiceDI: TypeAlias = Annotated[ActivityService, Depends(activity_service_factory)]


def iyow_activity_service_factory(
    activity_repo: ActivityRepositoryDI,
    iyow_activity_repo: IyowActivityRepositoryDI,
    membership_repo: MembershipRepositoryDI,
) -> IyowActivityService:
    """Creates the IYOW activity service for the current request."""
    return IyowActivityService(activity_repo, iyow_activity_repo, membership_repo)


IyowActivityServiceDI: TypeAlias = Annotated[IyowActivityService, Depends(iyow_activity_service_factory)]


def iyow_submission_service_factory(
    activity_repo: ActivityRepositoryDI,
    iyow_activity_repo: IyowActivityRepositoryDI,
    submission_repo: SubmissionRepositoryDI,
    iyow_submission_repo: IyowSubmissionRepositoryDI,
    async_job_repo: AsyncJobRepositoryDI,
    membership_repo: MembershipRepositoryDI,
    job_queue: JobQueueDI,
) -> IyowSubmissionService:
    """Creates the IYOW submission service for the current request."""
    return IyowSubmissionService(
        activity_repo,
        iyow_activity_repo,
        submission_repo,
        iyow_submission_repo,
        async_job_repo,
        membership_repo,
        job_queue,
    )


IyowSubmissionServiceDI: TypeAlias = Annotated[IyowSubmissionService, Depends(iyow_submission_service_factory)]


def get_activity_by_path_id(
    activity_id: Annotated[int, Path()],
    activity_repo: ActivityRepositoryDI,
) -> Activity:
    """Loads an activity from the activity_id path parameter.

    Args:
        activity_id: Activity identifier from the request path.
        activity_repo: Repository used to load activities.

    Returns:
        The matching activity.

    Raises:
        HTTPException: If the activity does not exist.
    """
    activity = activity_repo.get_by_id(activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found.")
    return activity


ActivityByPathDI: TypeAlias = Annotated[Activity, Depends(get_activity_by_path_id)]
