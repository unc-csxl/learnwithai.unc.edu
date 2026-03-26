"""Joke generation tool — models, tables, and service.

The ``JokeGenerationJobHandler`` is intentionally **not** re-exported
here to avoid a circular import with ``learnwithai.jobs``. Import it
directly from ``learnwithai.tools.jokes.job`` when needed.
"""

from .models import (
    JOKE_GENERATION_KIND,
    JokeGenerationInput,
    JokeGenerationJob,
    JokeGenerationOutput,
)
from .service import JokeGenerationService
from .tables import JokeRequest

__all__ = [
    "JOKE_GENERATION_KIND",
    "JokeGenerationInput",
    "JokeGenerationJob",
    "JokeGenerationOutput",
    "JokeGenerationService",
    "JokeRequest",
]
