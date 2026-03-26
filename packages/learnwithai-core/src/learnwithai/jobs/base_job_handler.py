"""Reusable base class for background job handlers.

Owns session lifecycle (open, commit/rollback, close), PROCESSING
status transition, and best-effort notification so that concrete
handlers only implement domain-specific ``_execute`` logic.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Generic, TypeVar

from sqlmodel import Session

from ..config import Settings
from ..interfaces import JobHandler, JobNotifier, JobUpdate, TrackedJob
from ..repositories.async_job_repository import AsyncJobRepository
from ..tables.async_job import AsyncJobStatus

logger = logging.getLogger(__name__)

JobT = TypeVar("JobT", bound=TrackedJob)


class BaseJobHandler(JobHandler[JobT], Generic[JobT]):
    """Manages session lifecycle and notification around job execution.

    Subclasses implement :meth:`_execute` with their domain-specific
    logic.  The base class handles:

    * Opening and closing a ``Session``
    * Transitioning the job to ``PROCESSING`` and notifying
    * Committing on success and notifying the final status
    * Rolling back on failure, marking ``FAILED``, and notifying

    Concrete handlers receive the open session directly in
    :meth:`_execute` and construct whatever repositories or services
    they need inside the handler. This keeps worker wiring explicit and
    avoids a separate dependency injection layer inside core.

    The ``job`` payload must expose a ``job_id: int`` attribute that
    maps to an :class:`~learnwithai.tables.async_job.AsyncJob` row.
    """

    def handle(self, job: JobT) -> None:
        """Runs the full handler lifecycle for a single job.

        Opens a session, transitions to PROCESSING, calls ``_execute``
        with that live session, and manages commit/rollback.

        Args:
            job: Typed job payload containing at least ``job_id``.
        """
        from sqlmodel import Session as _Session

        from ..config import get_settings
        from ..db import get_engine

        settings = get_settings()
        notifier = self._build_notifier(settings)

        engine = get_engine()
        with _Session(engine) as session:
            async_job_repo = AsyncJobRepository(session)

            try:
                self._set_processing(job.job_id, async_job_repo, session, notifier)
                self._execute(job, session)
                session.commit()
                self._notify(notifier, job.job_id, async_job_repo)
            except Exception:
                session.rollback()
                self._mark_failed(job.job_id, async_job_repo)
                session.commit()
                self._notify(notifier, job.job_id, async_job_repo)
                raise

    @abstractmethod
    def _execute(self, job: JobT, session: Session) -> None:
        """Subclasses implement domain-specific job logic here.

        The session is open and a ``PROCESSING`` status has already been
        set. Construct any repositories or services you need directly
        from this session inside the handler. Raising an exception
        triggers rollback and ``FAILED`` marking.

        Args:
            job: Typed job payload.
            session: Open database session shared by the full handler.
        """

    def _build_notifier(self, settings: Settings) -> JobNotifier:
        """Creates the notifier used for status-change broadcasts.

        Override in tests or alternate environments to supply a
        different notifier (e.g. :class:`NoOpJobNotifier`).

        Args:
            settings: Application settings for connection details.

        Returns:
            A notifier suitable for the current runtime.
        """
        from learnwithai_jobqueue.rabbitmq_job_notifier import RabbitMQJobNotifier

        return RabbitMQJobNotifier(settings.effective_rabbitmq_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _set_processing(
        self,
        job_id: int,
        async_job_repo: AsyncJobRepository,
        session: Session,
        notifier: JobNotifier,
    ) -> None:
        """Transitions the job to PROCESSING, flushes, and notifies.

        The flush writes the status change to the database within the
        current transaction so the subsequent ``_notify()`` reads the
        correct state.  External database connections will not see
        ``PROCESSING`` until the handler commits after ``_execute()``
        returns.  This is intentional: the RabbitMQ notification
        provides an early signal, but the database row is only durably
        visible after the full operation succeeds.

        Args:
            job_id: Primary key of the AsyncJob to update.
            async_job_repo: Repository for job persistence.
            session: Open session to flush within.
            notifier: Notifier for broadcasting the status change.
        """
        async_job = async_job_repo.get_by_id(job_id)
        if async_job is not None:
            async_job.status = AsyncJobStatus.PROCESSING
            async_job_repo.update(async_job)
            session.flush()
            self._notify(notifier, job_id, async_job_repo)

    def _mark_failed(
        self,
        job_id: int,
        async_job_repo: AsyncJobRepository,
    ) -> None:
        """Marks the job as FAILED with a completion timestamp.

        Best-effort: swallows all exceptions so that marking never
        hides the original error.

        Args:
            job_id: Primary key of the AsyncJob to mark.
            async_job_repo: Repository for job persistence.
        """
        try:
            async_job = async_job_repo.get_by_id(job_id)
            if async_job is not None:
                async_job.status = AsyncJobStatus.FAILED
                async_job.completed_at = datetime.now(timezone.utc)
                async_job_repo.update(async_job)
        except Exception:
            pass

    def _notify(
        self,
        notifier: JobNotifier,
        job_id: int,
        async_job_repo: AsyncJobRepository,
    ) -> None:
        """Broadcasts the current job status via the notifier.

        Best-effort: swallows all exceptions so notification failures
        never crash the handler.

        Args:
            notifier: Publisher to send the update through.
            job_id: Primary key of the job to look up.
            async_job_repo: Repository used to reload the job state.
        """
        try:
            reloaded = async_job_repo.get_by_id(job_id)
            if reloaded is not None:
                notifier.notify(
                    JobUpdate(
                        job_id=job_id,
                        course_id=reloaded.course_id,
                        user_id=reloaded.created_by_pid,
                        kind=reloaded.kind,
                        status=reloaded.status.value,
                    )
                )
        except Exception:
            pass
