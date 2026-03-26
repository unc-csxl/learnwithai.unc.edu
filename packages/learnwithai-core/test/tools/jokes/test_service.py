"""Tests for the JokeGenerationService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from learnwithai.tables.async_job import AsyncJob, AsyncJobStatus
from learnwithai.tools.jokes.entities import JOKE_GENERATION_KIND
from learnwithai.tools.jokes.service import JokeGenerationService


def _make_service(
    async_job_repo: MagicMock | None = None,
    job_queue: MagicMock | None = None,
) -> JokeGenerationService:
    return JokeGenerationService(
        async_job_repo=async_job_repo or MagicMock(),
        job_queue=job_queue or MagicMock(),
    )


def test_create_request_creates_job_and_enqueues() -> None:
    subject = MagicMock()
    subject.pid = 222222222
    created_job = MagicMock(spec=AsyncJob)
    created_job.id = 42
    async_job_repo = MagicMock()
    async_job_repo.create.return_value = created_job
    job_queue = MagicMock()
    svc = _make_service(async_job_repo=async_job_repo, job_queue=job_queue)

    result = svc.create_request(subject, course_id=1, prompt="Jokes about recursion")

    assert result is created_job
    async_job_repo.create.assert_called_once()
    created_async_job = async_job_repo.create.call_args[0][0]
    assert created_async_job.course_id == 1
    assert created_async_job.created_by_pid == 222222222
    assert created_async_job.kind == JOKE_GENERATION_KIND
    assert created_async_job.status == AsyncJobStatus.PENDING
    assert created_async_job.input_data == {"prompt": "Jokes about recursion"}
    job_queue.enqueue.assert_called_once()


def test_list_requests_delegates_to_repo() -> None:
    async_job_repo = MagicMock()
    expected = [MagicMock(spec=AsyncJob)]
    async_job_repo.list_by_course_and_kind.return_value = expected
    svc = _make_service(async_job_repo=async_job_repo)

    result = svc.list_requests(course_id=1)

    assert result is expected
    async_job_repo.list_by_course_and_kind.assert_called_once_with(1, JOKE_GENERATION_KIND)


def test_get_request_delegates_to_repo() -> None:
    async_job_repo = MagicMock()
    expected = MagicMock(spec=AsyncJob)
    async_job_repo.get_by_id.return_value = expected
    svc = _make_service(async_job_repo=async_job_repo)

    result = svc.get_request(42)

    assert result is expected
    async_job_repo.get_by_id.assert_called_once_with(42)


def test_get_request_returns_none_when_not_found() -> None:
    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = None
    svc = _make_service(async_job_repo=async_job_repo)

    assert svc.get_request(999) is None


def test_delete_request_deletes_job() -> None:
    job = MagicMock(spec=AsyncJob)
    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = job
    svc = _make_service(async_job_repo=async_job_repo)

    svc.delete_request(42)

    async_job_repo.delete.assert_called_once_with(job)


def test_delete_request_raises_when_not_found() -> None:
    async_job_repo = MagicMock()
    async_job_repo.get_by_id.return_value = None
    svc = _make_service(async_job_repo=async_job_repo)

    with pytest.raises(ValueError, match="not found"):
        svc.delete_request(999)
