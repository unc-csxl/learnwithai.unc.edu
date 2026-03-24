"""No-op job queue for contexts where job submission is not required."""

from ..interfaces import Job, JobQueue


class NoopJobQueue(JobQueue):
    """A job queue implementation that silently discards all enqueued jobs.

    Use this when constructing a service that requires a ``JobQueue`` but
    will never call ``submit_upload`` or any other method that enqueues jobs.
    The canonical example is a background job handler: it only calls
    ``process_upload`` and ``mark_failed``, so it passes ``NoopJobQueue()``
    to the service constructor instead of wiring in the real queue.
    """

    def enqueue(self, job: Job) -> None:
        """Accepts a job and discards it without side effects.

        Args:
            job: Job payload to be silently dropped.
        """
        pass
