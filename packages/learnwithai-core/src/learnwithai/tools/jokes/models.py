# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Pydantic models for joke generation job input, output, and payload."""

from typing import Literal

from pydantic import BaseModel

from ...interfaces import TrackedJob

JOKE_GENERATION_KIND = "joke_generation"


class JokeGenerationJob(TrackedJob):
    """Dramatiq job payload for joke generation requests."""

    type: Literal["joke_generation"] = "joke_generation"


class JokeGenerationInput(BaseModel):
    """Shape of ``AsyncJob.input_data`` for joke generation jobs."""

    prompt: str


class JokeGenerationOutput(BaseModel):
    """Shape of ``AsyncJob.output_data`` for joke generation jobs."""

    jokes: list[str]
