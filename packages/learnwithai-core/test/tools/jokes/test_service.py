"""Tests for the JokeGenerationService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tools.jokes.models import JOKE_GENERATION_KIND
from learnwithai.tools.jokes.service import JokeGenerationService
from learnwithai.tools.jokes.tables import JokeRequest


def _make_service(
    joke_request_repo: MagicMock | None = None,
    async_job_repo: MagicMock | None = None,
    job_queue: MagicMock | None = None,
) -> JokeGenerationService:
    return JokeGenerationService(
        joke_request_repo=joke_request_repo or MagicMock(),
        async_job_repo=async_job_repo or MagicMock(),
        job_queue=job_queue or MagicMock(),
    )


def test_create_request_creates_joke_request_and_enqueues() -> None:
    subject = MagicMock()
    subject.pid = 222222222
    created_async_job = MagicMock(spec=AsyncJob)
    created_async_job.id = 42
    async_job_repo = MagicMock()
    async_job_repo.create.return_value = created_async_job

    created_joke_request = MagicMock(spec=JokeRequest)
    created_joke_request.id = 10
    joke_request_repo = MagicMock()
    joke_request_repo.create.return_value = created_joke_request

    job_queue = MagicMock()
    svc = _make_service(
        joke_request_repo=joke_request_repo,
        async_job_repo=async_job_repo,
        job_queue=job_queue,
    )

    result = svc.create_request(subject, course_id=1, prompt="Jokes about recursion")

    assert result is created_joke_request

    # Verify the async job was created with the correct fields
    async_job_repo.create.assert_called_once()
    created_aj = async_job_repo.create.call_args[0][0]
    assert created_aj.course_id == 1
    assert created_aj.created_by_pid == 222222222
    assert created_aj.kind == JOKE_GENERATION_KIND
    assert created_aj.status == AsyncJobStatus.PENDING

    # Verify the joke request was created
    joke_request_repo.create.assert_called_once()
    created_jr = joke_request_repo.create.call_args[0][0]
    assert created_jr.course_id == 1
    assert created_jr.created_by_pid == 222222222
    assert created_jr.prompt == "Jokes about recursion"
    assert created_jr.async_job_id == 42

    # Verify enqueue was called
    job_queue.enqueue.assert_called_once()


def test_list_requests_delegates_to_repo() -> None:
    joke_request_repo = MagicMock()
    expected = [MagicMock(spec=JokeRequest)]
    joke_request_repo.list_by_course.return_value = expected
    svc = _make_service(joke_request_repo=joke_request_repo)

    result = svc.list_requests(course_id=1)

    assert result is expected
    joke_request_repo.list_by_course.assert_called_once_with(1)


def test_get_request_delegates_to_repo() -> None:
    joke_request_repo = MagicMock()
    expected = MagicMock(spec=JokeRequest)
    joke_request_repo.get_by_id.return_value = expected
    svc = _make_service(joke_request_repo=joke_request_repo)

    result = svc.get_request(42)

    assert result is expected
    joke_request_repo.get_by_id.assert_called_once_with(42)


def test_get_request_returns_none_when_not_found() -> None:
    joke_request_repo = MagicMock()
    joke_request_repo.get_by_id.return_value = None
    svc = _make_service(joke_request_repo=joke_request_repo)

    assert svc.get_request(999) is None


def test_delete_request_deletes_joke_request_and_async_job() -> None:
    joke_request = MagicMock(spec=JokeRequest)
    joke_request.async_job_id = 42
    joke_request_repo = MagicMock()
    joke_request_repo.get_by_id.return_value = joke_request

    async_job = MagicMock(spec=AsyncJob)
    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = async_job

    svc = _make_service(joke_request_repo=joke_request_repo, async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.delete.assert_called_once_with(async_job)
    joke_request_repo.delete.assert_called_once_with(joke_request)


def test_delete_request_raises_when_not_found() -> None:
    joke_request_repo = MagicMock()
    joke_request_repo.get_by_id.return_value = None
    svc = _make_service(joke_request_repo=joke_request_repo)

    with pytest.raises(ValueError, match="not found"):
        svc.delete_request(999)


def test_delete_request_handles_missing_async_job() -> None:
    joke_request = MagicMock(spec=JokeRequest)
    joke_request.async_job_id = 42
    joke_request_repo = MagicMock()
    joke_request_repo.get_by_id.return_value = joke_request

    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = None

    svc = _make_service(joke_request_repo=joke_request_repo, async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.delete.assert_not_called()
    joke_request_repo.delete.assert_called_once_with(joke_request)


def test_delete_request_handles_no_async_job_id() -> None:
    joke_request = MagicMock(spec=JokeRequest)
    joke_request.async_job_id = None
    joke_request_repo = MagicMock()
    joke_request_repo.get_by_id.return_value = joke_request

    async_job_repo = MagicMock()
    svc = _make_service(joke_request_repo=joke_request_repo, async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.get_by_id.assert_not_called()
    joke_request_repo.delete.assert_called_once_with(joke_request)
