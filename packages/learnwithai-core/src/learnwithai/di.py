"""Dependency factories shared across API routes and job handlers.

The pure factories in this module build repositories and services from
already-resolved dependencies. FastAPI consumers use the ``*DI`` type
aliases below for request-scoped injection. Background job handlers use
the worker-only ``*_handler_factory`` helpers near the bottom of the
module with ``fast-depends``.

Route-specific concerns such as authentication, path lookups, and query
parameter parsing remain in ``api.di``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, TypeAlias

from fast_depends import Depends as HandlerDepends
from fastapi import Depends as FastAPIDepends
from sqlmodel import Session

from .config import Settings
from .db import get_session
from .interfaces import JobQueue
from .repositories.async_job_repository import AsyncJobRepository
from .repositories.course_repository import CourseRepository
from .repositories.membership_repository import MembershipRepository
from .repositories.user_repository import UserRepository
from .services.course_service import CourseService

if TYPE_CHECKING:
    from .services.roster_upload_service import RosterUploadService

SessionDI: TypeAlias = Annotated[Session, FastAPIDepends(get_session)]


def settings_factory() -> Settings:
    """Builds a settings object for dependency injection."""
    return Settings()


SettingsDI: TypeAlias = Annotated[Settings, FastAPIDepends(settings_factory)]


def user_repository_factory(session: SessionDI) -> UserRepository:
    """Constructs a user repository bound to *session*."""
    return UserRepository(session)


UserRepositoryDI: TypeAlias = Annotated[
    UserRepository, FastAPIDepends(user_repository_factory)
]


def course_repository_factory(session: SessionDI) -> CourseRepository:
    """Constructs a course repository bound to *session*."""
    return CourseRepository(session)


CourseRepositoryDI: TypeAlias = Annotated[
    CourseRepository, FastAPIDepends(course_repository_factory)
]


def membership_repository_factory(session: SessionDI) -> MembershipRepository:
    """Constructs a membership repository bound to *session*."""
    return MembershipRepository(session)


MembershipRepositoryDI: TypeAlias = Annotated[
    MembershipRepository, FastAPIDepends(membership_repository_factory)
]


def async_job_repository_factory(session: SessionDI) -> AsyncJobRepository:
    """Constructs an async job repository bound to *session*."""
    return AsyncJobRepository(session)


AsyncJobRepositoryDI: TypeAlias = Annotated[
    AsyncJobRepository, FastAPIDepends(async_job_repository_factory)
]


def course_service_factory(
    course_repo: CourseRepositoryDI,
    membership_repo: MembershipRepositoryDI,
) -> CourseService:
    """Creates a course service with its repository dependencies."""
    return CourseService(course_repo, membership_repo)


CourseServiceDI: TypeAlias = Annotated[
    CourseService, FastAPIDepends(course_service_factory)
]


def forbidden_job_queue_factory() -> JobQueue:
    """Returns a :class:`ForbiddenJobQueue` for handler contexts."""
    from .jobs.forbidden_job_queue import ForbiddenJobQueue

    return ForbiddenJobQueue()


def roster_upload_service_factory(
    async_job_repo: AsyncJobRepository,
    user_repo: UserRepository,
    membership_repo: MembershipRepository,
    job_queue: JobQueue,
) -> "RosterUploadService":
    """Creates a roster upload service with all dependencies."""
    from .services.roster_upload_service import RosterUploadService

    return RosterUploadService(async_job_repo, user_repo, membership_repo, job_queue)


def async_job_repository_handler_factory(
    session: Session = HandlerDepends(get_session),
) -> AsyncJobRepository:
    """Builds an async job repository in a job handler context."""
    return async_job_repository_factory(session)


def user_repository_handler_factory(
    session: Session = HandlerDepends(get_session),
) -> UserRepository:
    """Builds a user repository in a job handler context."""
    return user_repository_factory(session)


def membership_repository_handler_factory(
    session: Session = HandlerDepends(get_session),
) -> MembershipRepository:
    """Builds a membership repository in a job handler context."""
    return membership_repository_factory(session)


def roster_upload_service_handler_factory(
    async_job_repo: AsyncJobRepository = HandlerDepends(
        async_job_repository_handler_factory
    ),
    user_repo: UserRepository = HandlerDepends(user_repository_handler_factory),
    membership_repo: MembershipRepository = HandlerDepends(
        membership_repository_handler_factory
    ),
    job_queue: JobQueue = HandlerDepends(forbidden_job_queue_factory),
) -> "RosterUploadService":
    """Builds a roster upload service in a job handler context."""
    return roster_upload_service_factory(
        async_job_repo, user_repo, membership_repo, job_queue
    )
