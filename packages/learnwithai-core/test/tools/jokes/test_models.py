"""Tests for joke generation entities."""

from learnwithai.tools.jokes.models import (
    JOKE_GENERATION_KIND,
    JokeGenerationInput,
    JokeGenerationOutput,
)


def test_joke_generation_kind_constant() -> None:
    assert JOKE_GENERATION_KIND == "joke_generation"


def test_joke_generation_input_round_trips() -> None:
    model = JokeGenerationInput(prompt="Tell me jokes about recursion")
    data = model.model_dump()
    assert data == {"prompt": "Tell me jokes about recursion"}
    restored = JokeGenerationInput.model_validate(data)
    assert restored.prompt == "Tell me jokes about recursion"


def test_joke_generation_output_round_trips() -> None:
    model = JokeGenerationOutput(jokes=["Joke 1", "Joke 2"])
    data = model.model_dump()
    assert data == {"jokes": ["Joke 1", "Joke 2"]}
    restored = JokeGenerationOutput.model_validate(data)
    assert restored.jokes == ["Joke 1", "Joke 2"]
