"""
Run the Worker via `dramatic`:

uv run --package learnwithai-jobqueue dramatiq learnwithai_jobqueue.worker
"""

# The following line is needed to register the dispatcher and dramatiq actor
import learnwithai_jobqueue.dramatiq_job_queue  # noqa: F401

print("Worker Ready")
