"""Imports all SQLModel table modules so metadata registration is explicit."""

from .course import Course
from .membership import Membership
from .roster_upload_job import RosterUploadJob
from .user import User

__all__ = ["Course", "Membership", "RosterUploadJob", "User"]
