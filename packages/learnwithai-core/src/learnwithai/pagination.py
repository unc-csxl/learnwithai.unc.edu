# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Pagination primitives shared across services and repositories."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class PaginationParams:
    """Carries page number and page size through the call stack."""

    page: int = 1
    page_size: int = 25


class PaginatedResult(BaseModel, Generic[T]):
    """Wraps a page of items with total count and pagination metadata."""

    items: list[T]
    total: int
    page: int
    page_size: int
