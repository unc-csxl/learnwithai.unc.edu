"""Tests for the OpenAIService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from learnwithai.tools.jokes.openai_service import OpenAIService


def _mock_completion(content: str) -> MagicMock:
    """Creates a mock ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_returns_parsed_lines(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion(
        "Why did the function go to therapy?\n"
        "Because it had too many issues to resolve.\n"
        "I told my compiler a joke — it didn't get it.\n"
    )
    svc = OpenAIService(api_key="sk-test", model="gpt-4o-mini")

    result = svc.generate_jokes("Jokes about compilers", count=3)

    assert result == [
        "Why did the function go to therapy?",
        "Because it had too many issues to resolve.",
        "I told my compiler a joke — it didn't get it.",
    ]
    mock_client.chat.completions.create.assert_called_once()


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_strips_numbering(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion(
        "1. First joke\n2. Second joke\n3. Third joke\n"
    )
    svc = OpenAIService(api_key="sk-test")

    result = svc.generate_jokes("topic", count=5)

    assert result == ["First joke", "Second joke", "Third joke"]


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_limits_to_count(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("Joke A\nJoke B\nJoke C\nJoke D\nJoke E\n")
    svc = OpenAIService(api_key="sk-test")

    result = svc.generate_jokes("topic", count=3)

    assert len(result) == 3


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_handles_empty_response(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("")
    svc = OpenAIService(api_key="sk-test")

    result = svc.generate_jokes("topic")

    assert result == []


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_handles_none_content(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    choice = MagicMock()
    choice.message.content = None
    resp = MagicMock()
    resp.choices = [choice]
    mock_client.chat.completions.create.return_value = resp
    svc = OpenAIService(api_key="sk-test")

    result = svc.generate_jokes("topic")

    assert result == []


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_skips_blank_lines(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("Joke A\n\n\nJoke B\n   \nJoke C")
    svc = OpenAIService(api_key="sk-test")

    result = svc.generate_jokes("topic", count=5)

    assert result == ["Joke A", "Joke B", "Joke C"]


@patch("learnwithai.tools.jokes.openai_service.openai.OpenAI")
def test_generate_jokes_skips_numbering_only_lines(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("1. Joke A\n2.\n3. Joke C")
    svc = OpenAIService(api_key="sk-test")

    result = svc.generate_jokes("topic", count=5)

    assert result == ["Joke A", "Joke C"]
