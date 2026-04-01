# learnwithai-jobqueue

`learnwithai-jobqueue` connects shared jobs from `learnwithai-core` to the actual queue infrastructure.

If `learnwithai-core` explains what background work should happen, this package explains how that work gets delivered and executed.

## What This Package Owns

This package contains the infrastructure pieces for background work:

- Dramatiq broker setup
- queue adapter implementations
- RabbitMQ-based job notifications
- the worker entrypoint

## Directory Map

```text
src/learnwithai_jobqueue/
|- broker.py                Dramatiq broker configuration
|- dramatiq_job_queue.py    Queue adapter used by services
|- rabbitmq_job_notifier.py Publishes realtime job updates
`- worker.py                Worker process entrypoint
```

## How It Fits The System

The normal background-job flow looks like this:

1. A route or service decides work should happen asynchronously.
2. A job definition from `learnwithai-core` is enqueued.
3. This package sends that job to Dramatiq and RabbitMQ.
4. The worker process started from `worker.py` executes the job.
5. Job updates can be published back to the API's realtime layer.

You usually only need to edit this package when queue delivery, worker startup, or job-update publishing changes.

## Running The Worker

From the repository root:

```bash
uv run --package learnwithai-jobqueue dramatiq --processes 1 --threads 2 learnwithai_jobqueue.worker
```

Or use the `job queue: run` task in VS Code.

## Tests

Run tests from the repository root:

```bash
uv run pytest packages/learnwithai-jobqueue/test
```

Finish with the repository-wide check:

```bash
./scripts/qa.sh --check
```