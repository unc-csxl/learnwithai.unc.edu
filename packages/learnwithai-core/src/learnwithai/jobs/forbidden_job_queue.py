"""Forbidden job queue that raises on use, to expose misconfigured contexts."""

from ..interfaces import Job, JobQueue


class ForbiddenJobQueue(JobQueue):
    """A JobQueue implementation that raises if ``enqueue`` is ever called.

    Use this when constructing a service that must accept a ``JobQueue``
    dependency but is known never to submit jobs in that context.  If
    ``enqueue`` is called anyway, the ``RuntimeError`` immediately surfaces
    the programming error rather than silently dropping the job.

    The canonical example is a background job handler: it calls
    ``process_upload`` but never submits new jobs, so it passes
    ``ForbiddenJobQueue()`` to the service constructor.  Any code path that
    unexpectedly reaches ``enqueue`` is caught at the earliest opportunity.
    """

    def enqueue(self, job: Job) -> None:
        """Raise unconditionally to signal unexpected job submission.

        Args:
            job: The job that should never have been submitted.

        Raises:
            RuntimeError: Always — ``enqueue`` must not be called in this
                context.  Wire a real ``JobQueue`` implementation wherever
                job submission is required.
        """
        raise RuntimeError(
            f"ForbiddenJobQueue.enqueue was called with {job!r}. "
            "This context expected no job submission. "
            "Provide a real JobQueue implementation where jobs must be submitted."
        )
