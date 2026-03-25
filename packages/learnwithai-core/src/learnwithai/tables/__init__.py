"""Imports all SQLModel table modules so metadata registration is explicit."""

from .async_job import AsyncJob, AsyncJobStatus
from .course import Course
from .membership import Membership
from .user import User

__all__ = ["AsyncJob", "AsyncJobStatus", "Course", "Membership", "User"]
