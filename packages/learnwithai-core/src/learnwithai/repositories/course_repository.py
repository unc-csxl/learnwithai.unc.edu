# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Persistence helpers for course records."""

from ..tables.course import Course
from .base_repository import BaseRepository


class CourseRepository(BaseRepository[Course, int]):
    """Provides course lookup and persistence operations."""

    @property
    def model_type(self) -> type[Course]:
        """Returns the SQLModel class managed by this repository."""
        return Course
