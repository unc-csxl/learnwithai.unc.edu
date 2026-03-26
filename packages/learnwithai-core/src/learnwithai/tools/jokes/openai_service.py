"""Thin wrapper around the OpenAI Chat Completions API for joke generation."""

import openai

JOKE_SYSTEM_PROMPT = (
    "You are a witty comedy writer who specializes in educational humor. "
    "The user will describe a course topic and you will generate jokes "
    "related to that topic that an instructor could use to add humor to "
    "their lectures. Return exactly {count} jokes, one per line. Do not "
    "number them. Each joke should be self-contained and concise."
)


class OpenAIService:
    """Generates jokes via the OpenAI Chat Completions API.

    Attributes:
        _client: Configured OpenAI client.
        _model: Model identifier used for completions.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initializes the service with an API key and model.

        Args:
            api_key: OpenAI API key.
            model: Model to use for chat completions.
        """
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def generate_jokes(self, prompt: str, count: int = 5) -> list[str]:
        """Generates joke ideas for the given course content description.

        Args:
            prompt: Description of the topic to generate jokes about.
            count: Number of jokes to request.

        Returns:
            A list of joke strings.

        Raises:
            openai.OpenAIError: If the API call fails.
        """
        system_message = JOKE_SYSTEM_PROMPT.format(count=count)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return self._parse_jokes(content, count)

    def _parse_jokes(self, content: str, count: int) -> list[str]:
        """Splits the response content into individual jokes.

        Filters blank lines and strips leading numbering (e.g. ``1.``)
        in case the model numbers them despite instructions.

        Args:
            content: Raw response text from the model.
            count: Maximum number of jokes to return.

        Returns:
            A list of cleaned joke strings, at most *count* items.
        """
        lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
        jokes: list[str] = []
        for line in lines:
            # Strip leading numbering like "1. " or "1) "
            cleaned = line.lstrip("0123456789").lstrip(".)")
            cleaned = cleaned.strip()
            if cleaned:
                jokes.append(cleaned)
            if len(jokes) >= count:
                break
        return jokes
