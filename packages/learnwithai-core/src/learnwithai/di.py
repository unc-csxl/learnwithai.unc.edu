"""Dependency injection factories for background job handler contexts.

These factories use ``fast-depends`` for automatic dependency resolution
inside :class:`~learnwithai.jobs.base_job_handler.BaseJobHandler`
subclasses.  The API layer defines its own DI wiring with FastAPI's
native ``Depends`` in ``api.dependency_injection``.

In the handler context, :func:`get_session` is overridden so that all
repositories and services share the handler's own session.  See
:meth:`BaseJobHandler.handle` for the override mechanism.
"""

from fast_depends import Depends
from sqlmodel import Session

from .db import get_session
from .interfaces import JobQueue
from .repositories.async_job_repository import AsyncJobRepository
from .repositories.membership_repository import MembershipRepository
from .repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


def async_job_repo_factory(session: Session = Depends(get_session)) -> AsyncJobRepository:
    """Creates an :class:`AsyncJobRepository` bound to *session*."""
    return AsyncJobRepository(session)


def user_repo_factory(session: Session = Depends(get_session)) -> UserRepository:
    """Creates a :class:`UserRepository` bound to *session*."""
    return UserRepository(session)


def membership_repo_factory(session: Session = Depends(get_session)) -> MembershipRepository:
    """Creates a :class:`MembershipRepository` bound to *session*."""
    return MembershipRepository(session)

# ---------------------------------------------------------------------------
# Job Queue (worker context always uses ForbiddenJobQueue)
# ---------------------------------------------------------------------------


def forbidden_job_queue_factory() -> JobQueue:
    """Returns a :class:`ForbiddenJobQueue` for handler contexts."""
    from .jobs.forbidden_job_queue import ForbiddenJobQueue

    return ForbiddenJobQueue()

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def roster_upload_svc_factory(
    async_job_repo: AsyncJobRepository = Depends(async_job_repo_factory),
    user_repo: UserRepository = Depends(user_repo_factory),
    membership_repo: MembershipRepository = Depends(membership_repo_factory),
    job_queue: JobQueue = Depends(forbidden_job_queue_factory),
) -> "RosterUploadService":
    """Creates a :class:`RosterUploadService` with all dependencies."""
    from .services.roster_upload_service import RosterUploadService

    return RosterUploadService(async_job_repo, user_repo, membership_repo, job_queue)
