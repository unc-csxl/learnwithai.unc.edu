# learnwithai-jobqueue

`learnwithai-jobqueue` is the background work adapter for LearnWithAI. It connects queueable job definitions from `learnwithai-core` to Dramatiq and the configured RabbitMQ broker.

## What Lives Here

- `src/learnwithai_jobqueue/broker.py`: broker configuration
- `src/learnwithai_jobqueue/dramatiq_job_queue.py`: queue adapter implementation
- `src/learnwithai_jobqueue/worker.py`: worker process entrypoint
- `test/`: tests for the queue integration layer

## How It Fits In The System

Use this package when work should happen outside the request-response cycle.

Current examples include queue submission through the API health route and worker startup through the Dramatiq entrypoint.

## Running The Worker

From the repository root:

```bash
uv run --package learnwithai-jobqueue dramatiq learnwithai_jobqueue.worker
```

Or run the `job queue: run` task from VS Code.

## Testing

From the repository root:

```bash
uv run pytest packages/learnwithai-jobqueue/test
```

Finish with the repository QA check:

```bash
./scripts/qa.sh --check
```