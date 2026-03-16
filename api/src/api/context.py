"""Request context containers used by the API layer."""

from typing import Annotated, TypeAlias
from fastapi import Depends
from .dependency_injection import SessionDI, JobQueueDI


class PublicContext:
    """Provides dependencies that are safe to expose to unauthenticated handlers.

    Attributes:
        session: Database session scoped to the current request.
        job_queue: Queue adapter used to schedule background work.
    """

    def __init__(self, session: SessionDI, job_queue: JobQueueDI):
        """Initializes a public request context.

        Args:
            session: Database session for the current request.
            job_queue: Queue adapter for background jobs.
        """
        self.session = session
        self.job_queue = job_queue


class UserContext:
    """Provides dependencies for authenticated handlers.

    Attributes:
        session: Database session scoped to the current request.
        job_queue: Queue adapter used to schedule background work.
    """

    def __init__(self, session: SessionDI, job_queue: JobQueueDI):
        """Initializes an authenticated request context.

        Args:
            session: Database session for the current request.
            job_queue: Queue adapter for background jobs.
        """
        self.session = session
        self.job_queue = job_queue


PublicContextDI: TypeAlias = Annotated[PublicContext, Depends()]
UserContextDI: TypeAlias = Annotated[UserContext, Depends()]
