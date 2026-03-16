"""
Run the Worker via `dramatic`:

uv run --package learnwithai-jobqueue dramatiq learnwithai_jobqueue.worker
"""

import logging
import learnwithai_jobqueue.dramatiq_job_queue  # noqa: F401

logger = logging.getLogger(__name__)
logger.info("Worker Ready")
