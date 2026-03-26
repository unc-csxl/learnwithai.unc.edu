"""Tests for the JokeGenerationService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tools.jokes.models import JOKE_GENERATION_KIND
from learnwithai.tools.jokes.service import JokeGenerationService
from learnwithai.tools.jokes.tables import Joke


def _make_service(
    joke_repo: MagicMock | None = None,
    async_job_repo: MagicMock | None = None,
    job_queue: MagicMock | None = None,
) -> JokeGenerationService:
    return JokeGenerationService(
        joke_repo=joke_repo or MagicMock(),
        async_job_repo=async_job_repo or MagicMock(),
        job_queue=job_queue or MagicMock(),
    )


def test_create_request_creates_joke_and_enqueues() -> None:
    subject = MagicMock()
    subject.pid = 222222222
    created_async_job = MagicMock(spec=AsyncJob)
    created_async_job.id = 42
    async_job_repo = MagicMock()
    async_job_repo.create.return_value = created_async_job

    created_joke = MagicMock(spec=Joke)
    created_joke.id = 10
    joke_repo = MagicMock()
    joke_repo.create.return_value = created_joke

    job_queue = MagicMock()
    svc = _make_service(
        joke_repo=joke_repo,
        async_job_repo=async_job_repo,
        job_queue=job_queue,
    )

    result = svc.create_request(subject, course_id=1, prompt="Jokes about recursion")

    assert result is created_joke

    # Verify the async job was created with the correct fields
    async_job_repo.create.assert_called_once()
    created_aj = async_job_repo.create.call_args[0][0]
    assert created_aj.course_id == 1
    assert created_aj.created_by_pid == 222222222
    assert created_aj.kind == JOKE_GENERATION_KIND
    assert created_aj.status == AsyncJobStatus.PENDING

    # Verify the joke was created
    joke_repo.create.assert_called_once()
    created_j = joke_repo.create.call_args[0][0]
    assert created_j.course_id == 1
    assert created_j.created_by_pid == 222222222
    assert created_j.prompt == "Jokes about recursion"
    assert created_j.async_job_id == 42

    # Verify enqueue was called
    job_queue.enqueue.assert_called_once()


def test_list_requests_delegates_to_repo() -> None:
    joke_repo = MagicMock()
    expected = [MagicMock(spec=Joke)]
    joke_repo.list_by_course.return_value = expected
    svc = _make_service(joke_repo=joke_repo)

    result = svc.list_requests(course_id=1)

    assert result is expected
    joke_repo.list_by_course.assert_called_once_with(1)


def test_list_requests_with_jobs_delegates_to_repo() -> None:
    joke_repo = MagicMock()
    expected = [MagicMock(spec=Joke)]
    joke_repo.list_by_course_with_jobs.return_value = expected
    svc = _make_service(joke_repo=joke_repo)

    result = svc.list_requests_with_jobs(course_id=1)

    assert result is expected
    joke_repo.list_by_course_with_jobs.assert_called_once_with(1)


def test_get_request_delegates_to_repo() -> None:
    joke_repo = MagicMock()
    expected = MagicMock(spec=Joke)
    joke_repo.get_by_id.return_value = expected
    svc = _make_service(joke_repo=joke_repo)

    result = svc.get_request(42)

    assert result is expected
    joke_repo.get_by_id.assert_called_once_with(42)


def test_get_request_returns_none_when_not_found() -> None:
    joke_repo = MagicMock()
    joke_repo.get_by_id.return_value = None
    svc = _make_service(joke_repo=joke_repo)

    assert svc.get_request(999) is None


def test_delete_request_deletes_joke_and_async_job() -> None:
    joke = MagicMock(spec=Joke)
    joke.async_job_id = 42
    joke_repo = MagicMock()
    joke_repo.get_by_id.return_value = joke

    async_job = MagicMock(spec=AsyncJob)
    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = async_job

    svc = _make_service(joke_repo=joke_repo, async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.delete.assert_called_once_with(async_job)
    joke_repo.delete.assert_called_once_with(joke)


def test_delete_request_raises_when_not_found() -> None:
    joke_repo = MagicMock()
    joke_repo.get_by_id.return_value = None
    svc = _make_service(joke_repo=joke_repo)

    with pytest.raises(ValueError, match="not found"):
        svc.delete_request(999)


def test_delete_request_handles_missing_async_job() -> None:
    joke = MagicMock(spec=Joke)
    joke.async_job_id = 42
    joke_repo = MagicMock()
    joke_repo.get_by_id.return_value = joke

    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = None

    svc = _make_service(joke_repo=joke_repo, async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.delete.assert_not_called()
    joke_repo.delete.assert_called_once_with(joke)


def test_delete_request_handles_no_async_job_id() -> None:
    joke = MagicMock(spec=Joke)
    joke.async_job_id = None
    joke_repo = MagicMock()
    joke_repo.get_by_id.return_value = joke

    async_job_repo = MagicMock()
    svc = _make_service(joke_repo=joke_repo, async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.get_by_id.assert_not_called()
    joke_repo.delete.assert_called_once_with(joke)
