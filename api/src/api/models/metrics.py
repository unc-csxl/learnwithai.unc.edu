# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""API response models for operations metrics."""

from pydantic import BaseModel


class UsageMetricsResponse(BaseModel):
    """Monthly usage statistics returned by the metrics endpoint."""

    month_label: str
    active_users: int
    active_courses: int
    submissions: int
    jobs_run: int
