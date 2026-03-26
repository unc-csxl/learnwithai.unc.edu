"""Tests for joke generation route handlers."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from learnwithai.errors import AuthorizationError
from learnwithai.tables.async_job import AsyncJobStatus
from learnwithai.tools.jokes.tables import Joke

from api.di import (
    course_service_factory,
    get_authenticated_user,
    get_course_by_path_id,
    joke_generation_service_factory,
)
from api.main import app
from api.models import JokeResponse
from api.routes.joke_generation import (
    create_joke_request,
    delete_joke_request,
    get_joke_request,
    list_joke_requests,
)

# ---- helpers ----


def _stub_user(pid: int = 123456789) -> MagicMock:
    mock = MagicMock()
    mock.pid = pid
    return mock


def _stub_course(course_id: int = 1) -> MagicMock:
    mock = MagicMock()
    mock.id = course_id
    return mock


def _stub_joke(
    joke_id: int = 1,
    course_id: int = 1,
    prompt: str = "Jokes about recursion",
    jokes: list[str] | None = None,
    async_job_id: int | None = 100,
    async_job_status: AsyncJobStatus = AsyncJobStatus.PENDING,
    async_job_completed_at: datetime | None = None,
) -> MagicMock:
    mock = MagicMock(spec=Joke)
    mock.id = joke_id
    mock.course_id = course_id
    mock.prompt = prompt
    mock.jokes = jokes or []
    mock.async_job_id = async_job_id
    mock.created_by_pid = 123456789
    mock.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    if async_job_id is not None:
        job_mock = MagicMock()
        job_mock.id = async_job_id
        job_mock.status = async_job_status
        job_mock.completed_at = async_job_completed_at
        mock.async_job = job_mock
    else:
        mock.async_job = None
    return mock


# ---- create_joke_request ----


def test_create_joke_request_returns_accepted_response() -> None:
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    joke_svc = MagicMock()
    created = _stub_joke(joke_id=42)
    joke_svc.create_request.return_value = created
    body = MagicMock()
    body.prompt = "Jokes about recursion"

    result = create_joke_request(subject, course, body, course_svc, joke_svc)

    assert isinstance(result, JokeResponse)
    assert result.id == 42
    assert result.job is not None
    assert result.job.status == AsyncJobStatus.PENDING
    assert result.prompt == "Jokes about recursion"
    course_svc.authorize_instructor.assert_called_once_with(subject, course)
    joke_svc.create_request.assert_called_once_with(subject, course.id, "Jokes about recursion")


def test_create_joke_request_raises_403_for_non_instructor() -> None:
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    course_svc.authorize_instructor.side_effect = AuthorizationError("nope")
    joke_svc = MagicMock()
    body = MagicMock()
    body.prompt = "topic"

    with pytest.raises(AuthorizationError):
        create_joke_request(subject, course, body, course_svc, joke_svc)


def test_get_joke_request_returns_none_job_when_no_async_job() -> None:
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    joke_svc = MagicMock()
    jr = _stub_joke(joke_id=42, course_id=1, async_job_id=None)
    joke_svc.get_request.return_value = jr

    result = get_joke_request(subject, course, course_svc, joke_svc, 42)

    assert result.job is None


def test_get_joke_request_returns_none_job_when_async_job_missing() -> None:
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    joke_svc = MagicMock()
    jr = _stub_joke(joke_id=42, course_id=1, async_job_id=None)
    joke_svc.get_request.return_value = jr

    result = get_joke_request(subject, course, course_svc, joke_svc, 42)

    assert result.job is None


# ---- list_joke_requests ----


def test_list_joke_requests_returns_list() -> None:
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    joke_svc = MagicMock()
    joke_svc.list_requests_with_jobs.return_value = [
        _stub_joke(joke_id=1, async_job_status=AsyncJobStatus.COMPLETED),
        _stub_joke(joke_id=2, jokes=["Ha!", "Ho!"], async_job_status=AsyncJobStatus.COMPLETED),
    ]

    result = list_joke_requests(subject, course, course_svc, joke_svc)

    assert len(result) == 2
    assert all(isinstance(r, JokeResponse) for r in result)
    assert result[1].jokes == ["Ha!", "Ho!"]
    course_svc.authorize_instructor.assert_called_once_with(subject, course)


def test_list_joke_requests_returns_empty_list() -> None:
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    joke_svc = MagicMock()
    joke_svc.list_requests_with_jobs.return_value = []

    result = list_joke_requests(subject, course, course_svc, joke_svc)

    assert result == []


# ---- get_joke_request ----


def test_get_joke_request_returns_job() -> None:
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    joke_svc = MagicMock()
    jr = _stub_joke(joke_id=42, course_id=1)
    joke_svc.get_request.return_value = jr

    result = get_joke_request(subject, course, course_svc, joke_svc, 42)

    assert isinstance(result, JokeResponse)
    assert result.id == 42


def test_get_joke_request_returns_404_when_not_found() -> None:
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    joke_svc = MagicMock()
    joke_svc.get_request.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_joke_request(subject, course, course_svc, joke_svc, 999)
    assert exc_info.value.status_code == 404


def test_get_joke_request_returns_404_for_wrong_course() -> None:
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    joke_svc = MagicMock()
    jr = _stub_joke(joke_id=42, course_id=99)
    joke_svc.get_request.return_value = jr

    with pytest.raises(HTTPException) as exc_info:
        get_joke_request(subject, course, course_svc, joke_svc, 42)
    assert exc_info.value.status_code == 404


# ---- delete_joke_request ----


def test_delete_joke_request_succeeds() -> None:
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    joke_svc = MagicMock()
    jr = _stub_joke(joke_id=42, course_id=1)
    joke_svc.get_request.return_value = jr

    delete_joke_request(subject, course, course_svc, joke_svc, 42)

    joke_svc.delete_request.assert_called_once_with(42)
    course_svc.authorize_instructor.assert_called_once_with(subject, course)


def test_delete_joke_request_returns_404_when_not_found() -> None:
    subject = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    joke_svc = MagicMock()
    joke_svc.get_request.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        delete_joke_request(subject, course, course_svc, joke_svc, 999)
    assert exc_info.value.status_code == 404


def test_delete_joke_request_returns_404_for_wrong_course() -> None:
    subject = _stub_user()
    course = _stub_course(course_id=1)
    course_svc = MagicMock()
    joke_svc = MagicMock()
    jr = _stub_joke(joke_id=42, course_id=99)
    joke_svc.get_request.return_value = jr

    with pytest.raises(HTTPException) as exc_info:
        delete_joke_request(subject, course, course_svc, joke_svc, 42)
    assert exc_info.value.status_code == 404


# ---- integration tests via TestClient ----


@pytest.fixture
def client():
    """TestClient for integration tests."""
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _override_common(
    joke_svc: MagicMock,
) -> None:
    """Applies common DI overrides shared by all integration tests."""
    user = _stub_user()
    course = _stub_course()
    course_svc = MagicMock()
    app.dependency_overrides[get_authenticated_user] = lambda: user
    app.dependency_overrides[get_course_by_path_id] = lambda: course
    app.dependency_overrides[course_service_factory] = lambda: course_svc
    app.dependency_overrides[joke_generation_service_factory] = lambda: joke_svc


@pytest.mark.integration
def test_create_joke_request_endpoint(client: TestClient) -> None:
    joke_svc = MagicMock()
    joke_svc.create_request.return_value = _stub_joke(joke_id=42)
    _override_common(joke_svc)

    response = client.post(
        "/api/courses/1/joke-requests",
        json={"prompt": "Jokes about recursion"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["id"] == 42
    assert body["job"]["status"] == "pending"
    assert body["prompt"] == "Jokes about recursion"


@pytest.mark.integration
def test_list_joke_requests_endpoint(client: TestClient) -> None:
    joke_svc = MagicMock()
    joke_svc.list_requests_with_jobs.return_value = [
        _stub_joke(joke_id=1, async_job_status=AsyncJobStatus.PENDING),
    ]
    _override_common(joke_svc)

    response = client.get("/api/courses/1/joke-requests")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == 1


@pytest.mark.integration
def test_get_joke_request_endpoint(client: TestClient) -> None:
    joke_svc = MagicMock()
    joke_svc.get_request.return_value = _stub_joke(joke_id=42, course_id=1)
    _override_common(joke_svc)

    response = client.get("/api/courses/1/joke-requests/42")

    assert response.status_code == 200
    assert response.json()["id"] == 42


@pytest.mark.integration
def test_delete_joke_request_endpoint(client: TestClient) -> None:
    joke_svc = MagicMock()
    joke_svc.get_request.return_value = _stub_joke(joke_id=42, course_id=1)
    _override_common(joke_svc)

    response = client.delete("/api/courses/1/joke-requests/42")

    assert response.status_code == 204
    joke_svc.delete_request.assert_called_once_with(42)
