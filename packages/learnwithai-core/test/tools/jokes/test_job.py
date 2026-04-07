# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the JokeGenerationJobHandler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from learnwithai.tools.jokes.job import JokeGenerationJobHandler, _parse_jokes
from learnwithai.tools.jokes.models import JokeGenerationJob


def test_joke_generation_job_type() -> None:
    job = JokeGenerationJob(job_id=1)
    assert job.type == "joke_generation"


def test_handler_calls_ai_service_and_stores_output() -> None:
    job_payload = JokeGenerationJob(job_id=42)
    handler = JokeGenerationJobHandler()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_notifier = MagicMock()

    # Mock the async job
    mock_async_job = MagicMock()
    mock_async_job.course_id = 1
    mock_async_job.created_by_pid = 222222222
    mock_async_job.kind = "joke_generation"
    mock_async_job.status = MagicMock(value="completed")

    # Mock the joke
    mock_joke = MagicMock()
    mock_joke.prompt = "Jokes about recursion"

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_joke_repo_cls = MagicMock()
    mock_joke_repo_instance = MagicMock()
    mock_joke_repo_instance.get_by_async_job_id.return_value = mock_joke
    mock_joke_repo_cls.return_value = mock_joke_repo_instance

    mock_ai_svc = MagicMock()
    mock_ai_svc.complete.return_value = "Joke 1\nJoke 2"

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-5-mini"

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
            "learnwithai.tools.jokes.job.JokeRepository",
            mock_joke_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "learnwithai.tools.jokes.job.AiCompletionService",
            return_value=mock_ai_svc,
        ),
    ):
        handler.handle(job_payload)

    mock_ai_svc.complete.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    # Jokes stored on joke
    assert mock_joke.jokes == ["Joke 1", "Joke 2"]
    # Raw data stored on async_job
    assert mock_async_job.output_data == {"raw_response": "Joke 1\nJoke 2"}


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
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(RuntimeError, match="openai_api_key is not configured"),
    ):
        handler.handle(job_payload)

    mock_session.rollback.assert_called_once()


def test_handler_rolls_back_on_ai_error() -> None:
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
    mock_async_job.input_data = {}
    mock_async_job.status = MagicMock(value="failed")

    mock_joke = MagicMock()
    mock_joke.prompt = "topic"

    mock_async_job_repo_cls = MagicMock()
    mock_async_job_repo_instance = MagicMock()
    mock_async_job_repo_instance.get_by_id.return_value = mock_async_job
    mock_async_job_repo_cls.return_value = mock_async_job_repo_instance

    mock_joke_repo_cls = MagicMock()
    mock_joke_repo_instance = MagicMock()
    mock_joke_repo_instance.get_by_async_job_id.return_value = mock_joke
    mock_joke_repo_cls.return_value = mock_joke_repo_instance

    mock_ai_svc = MagicMock()
    mock_ai_svc.complete.side_effect = RuntimeError("API error")

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-5-mini"

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
            "learnwithai.tools.jokes.job.JokeRepository",
            mock_joke_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "learnwithai.tools.jokes.job.AiCompletionService",
            return_value=mock_ai_svc,
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
    mock_settings.openai_model = "gpt-5-mini"

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


def test_handler_raises_when_joke_not_found() -> None:
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

    mock_joke_repo_cls = MagicMock()
    mock_joke_repo_instance = MagicMock()
    mock_joke_repo_instance.get_by_async_job_id.return_value = None
    mock_joke_repo_cls.return_value = mock_joke_repo_instance

    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test"
    mock_settings.openai_model = "gpt-5-mini"

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
            "learnwithai.tools.jokes.job.JokeRepository",
            mock_joke_repo_cls,
        ),
        patch(
            "learnwithai.tools.jokes.job.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="Joke for AsyncJob"),
    ):
        handler.handle(job_payload)


# --- _parse_jokes tests ---


def test_parse_jokes_splits_lines() -> None:
    result = _parse_jokes("Joke A\nJoke B\nJoke C", count=5)
    assert result == ["Joke A", "Joke B", "Joke C"]


def test_parse_jokes_strips_numbering() -> None:
    result = _parse_jokes("1. First joke\n2. Second joke\n3. Third joke", count=5)
    assert result == ["First joke", "Second joke", "Third joke"]


def test_parse_jokes_limits_to_count() -> None:
    result = _parse_jokes("A\nB\nC\nD\nE", count=3)
    assert len(result) == 3


def test_parse_jokes_handles_empty_string() -> None:
    assert _parse_jokes("", count=5) == []


def test_parse_jokes_skips_blank_lines() -> None:
    result = _parse_jokes("Joke A\n\n\nJoke B\n   \nJoke C", count=5)
    assert result == ["Joke A", "Joke B", "Joke C"]


def test_parse_jokes_skips_numbering_only_lines() -> None:
    result = _parse_jokes("1. Joke A\n2.\n3. Joke C", count=5)
    assert result == ["Joke A", "Joke C"]
