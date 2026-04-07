# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the AiCompletionService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from learnwithai.services.ai_completion_service import AiCompletionService


def _mock_completion(content: str) -> MagicMock:
    """Creates a mock ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("learnwithai.services.ai_completion_service.openai.AzureOpenAI")
def test_complete_returns_assistant_content(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("Hello, world!")
    svc = AiCompletionService(api_key="sk-test", model="gpt-5-mini")

    result = svc.complete(system_prompt="Be helpful.", user_prompt="Say hello.")

    assert result == "Hello, world!"
    mock_openai_cls.assert_called_once_with(
        api_key="sk-test",
        azure_endpoint="https://azureaiapi.cloud.unc.edu",
        api_version="2025-04-01-preview",
    )
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "Be helpful."},
            {"role": "user", "content": "Say hello."},
        ],
    )


@patch("learnwithai.services.ai_completion_service.openai.AzureOpenAI")
def test_complete_uses_model_override(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("response")
    svc = AiCompletionService(api_key="sk-test", model="gpt-5-mini")

    svc.complete(system_prompt="sys", user_prompt="usr", model="gpt-4o")

    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "gpt-4o"


@patch("learnwithai.services.ai_completion_service.openai.AzureOpenAI")
def test_complete_returns_empty_string_for_none_content(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    choice = MagicMock()
    choice.message.content = None
    response = MagicMock()
    response.choices = [choice]
    mock_client.chat.completions.create.return_value = response
    svc = AiCompletionService(api_key="sk-test")

    result = svc.complete(system_prompt="sys", user_prompt="usr")

    assert result == ""


@patch("learnwithai.services.ai_completion_service.openai.AzureOpenAI")
def test_complete_uses_default_model_when_no_override(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("ok")
    svc = AiCompletionService(api_key="sk-test", model="custom-model")

    svc.complete(system_prompt="sys", user_prompt="usr")

    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "custom-model"


@patch("learnwithai.services.ai_completion_service.openai.AzureOpenAI")
def test_complete_uses_custom_endpoint_and_api_version(mock_openai_cls: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("ok")

    AiCompletionService(
        api_key="sk-test",
        model="custom-model",
        endpoint="https://example.azure.com",
        api_version="2024-10-21",
    )

    mock_openai_cls.assert_called_once_with(
        api_key="sk-test",
        azure_endpoint="https://example.azure.com",
        api_version="2024-10-21",
    )
