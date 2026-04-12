# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Imports all SQLModel table modules so metadata registration is explicit."""

from .activity import Activity, ActivityType
from .async_job import AsyncJob, AsyncJobStatus
from .course import Course
from .membership import Membership
from .operator import Operator, OperatorPermission, OperatorRole
from .submission import Submission
from .user import User

__all__ = [
    "Activity",
    "ActivityType",
    "AsyncJob",
    "AsyncJobStatus",
    "Course",
    "Membership",
    "Operator",
    "OperatorPermission",
    "OperatorRole",
    "Submission",
    "User",
]
