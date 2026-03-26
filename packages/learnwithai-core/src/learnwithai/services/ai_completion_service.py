"""Shared AI chat-completion service wrapping the OpenAI client.

Provides a single abstraction that feature-specific services (joke
generation, quiz generation, tutoring, etc.) call instead of importing
the ``openai`` package directly.  Each call site can pass its own model
preference.
"""

import openai


class AiCompletionService:
    """Sends chat-completion requests via the OpenAI API.

    Attributes:
        _client: Configured OpenAI client.
        _model: Default model identifier used for completions.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initializes the service with an API key and default model.

        Args:
            api_key: OpenAI API key.
            model: Default model to use when callers do not override.
        """
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
    ) -> str:
        """Sends a chat completion request and returns the assistant message.

        Args:
            system_prompt: Instructions for the model.
            user_prompt: The user's input message.
            model: Optional model override; uses the default when ``None``.

        Returns:
            The text content of the assistant's reply.

        Raises:
            openai.OpenAIError: If the API call fails.
        """
        response = self._client.chat.completions.create(
            model=model or self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
