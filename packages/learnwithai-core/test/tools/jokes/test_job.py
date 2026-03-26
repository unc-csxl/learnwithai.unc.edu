"""Tests for the JokeGenerationJobHandler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from learnwithai.tools.jokes.entities import JokeGenerationJob
from learnwithai.tools.jokes.job import JokeGenerationJobHandler


def test_joke_generation_job_type() -> None:
    job = JokeGenerationJob(job_id=1)
    assert job.type == "joke_generation"


def test_handler_calls_openai_and_stores_output() -> None:
    job_payload = JokeGenerationJob(job_id=42)
    handler = JokeGenerationJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 222222222
    mock_async_job.kind = "joke_generation"
    mock_async_job.input_data = {"prompt": "Jokes about recursion"}
    mock_async_job.status = MagicMock(value="completed")

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_openai_svc = MagicMock()
    mock_openai_svc.generate_jokes.return_value = ["Joke 1", "Joke 2"]

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "learnwithai.tools.jokes.job.OpenAIService",
            return_value=mock_openai_svc,
        ),
    ):
        handler.handle(job_payload)

    mock_openai_svc.generate_jokes.assert_called_once_with("Jokes about recursion")
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    assert mock_async_job.output_data == {"jokes": ["Joke 1", "Joke 2"]}


def test_handler_raises_when_api_key_not_set() -> None:
    job_payload = JokeGenerationJob(job_id=42)
    handler = JokeGenerationJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 222222222
    mock_async_job.kind = "joke_generation"
    mock_async_job.status = MagicMock(value="failed")

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = None

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(RuntimeError, match="openai_api_key is not configured"),
    ):
        handler.handle(job_payload)

    mock_session.rollback.assert_called_once()


def test_handler_rolls_back_on_openai_error() -> None:
    job_payload = JokeGenerationJob(job_id=42)
    handler = JokeGenerationJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 222222222
    mock_async_job.kind = "joke_generation"
    mock_async_job.input_data = {"prompt": "topic"}
    mock_async_job.status = MagicMock(value="failed")

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_openai_svc = MagicMock()
    mock_openai_svc.generate_jokes.side_effect = RuntimeError("API error")

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.AsyncJobRepository",
            mock_async_job_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "learnwithai.tools.jokes.job.OpenAIService",
            return_value=mock_openai_svc,
        ),
        pytest.raises(RuntimeError, match="API error"),
    ):
        handler.handle(job_payload)

    mock_session.rollback.assert_called_once()


def test_handler_raises_when_async_job_not_found() -> None:
    job_payload = JokeGenerationJob(job_id=42)
    handler = JokeGenerationJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    # The base handler's repo returns a mock for set_processing,
    # but the handler's own repo returns None for the job lookup.
    base_async_job = MagicMock()
    base_async_job.course_id = 1
    base_async_job.created_by_pid = 222222222
    base_async_job.kind = "joke_generation"
    base_async_job.status = MagicMock(value="failed")

    base_repo_cls = MagicMock()
    base_repo_instance = MagicMock()
    base_repo_instance.get_by_id.return_value = base_async_job
    base_repo_cls.return_value = base_repo_instance

    handler_repo_cls = MagicMock()
    handler_repo_instance = MagicMock()
    handler_repo_instance.get_by_id.return_value = None
    handler_repo_cls.return_value = handler_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-4o-mini"

    with (
        patch.object(handler, "_build_notifier", return_value=mock_notifier),
        patch("learnwithai.db.get_engine", return_value=MagicMock()),
        patch("sqlmodel.Session", return_value=mock_session),
        patch(
            "learnwithai.jobs.base_job_handler.AsyncJobRepository",
            base_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.AsyncJobRepository",
            handler_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="not found"),
    ):
        handler.handle(job_payload)
