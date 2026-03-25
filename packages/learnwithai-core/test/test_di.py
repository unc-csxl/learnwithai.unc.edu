"""Tests for the shared core dependency injection factories."""

from unittest.mock import MagicMock

from learnwithai.di import (
    async_job_repository_factory,
    course_repository_factory,
    course_service_factory,
    forbidden_job_queue_factory,
    membership_repository_factory,
    roster_upload_service_factory,
    settings_factory,
    user_repository_factory,
)
from learnwithai.repositories.course_repository import CourseRepository
from learnwithai.jobs.forbidden_job_queue import ForbiddenJobQueue
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.services.course_service import CourseService
from learnwithai.services.roster_upload_service import RosterUploadService


def test_settings_factory() -> None:
    result = settings_factory()
    assert result.app_name == "learnwithai"


def test_async_job_repository_factory() -> None:
    session = MagicMock()
    result = async_job_repository_factory(session)
    assert isinstance(result, AsyncJobRepository)


def test_user_repository_factory() -> None:
    session = MagicMock()
    result = user_repository_factory(session)
    assert isinstance(result, UserRepository)


def test_course_repository_factory() -> None:
    session = MagicMock()
    result = course_repository_factory(session)
    assert isinstance(result, CourseRepository)


def test_membership_repository_factory() -> None:
    session = MagicMock()
    result = membership_repository_factory(session)
    assert isinstance(result, MembershipRepository)


def test_course_service_factory() -> None:
    course_repo = MagicMock()
    membership_repo = MagicMock()
    result = course_service_factory(course_repo, membership_repo)
    assert isinstance(result, CourseService)


def test_forbidden_job_queue_factory() -> None:
    result = forbidden_job_queue_factory()
    assert isinstance(result, ForbiddenJobQueue)


def test_roster_upload_service_factory() -> None:
    repo = MagicMock()
    user_repo = MagicMock()
    membership_repo = MagicMock()
    job_queue = MagicMock()
    result = roster_upload_service_factory(repo, user_repo, membership_repo, job_queue)
    assert isinstance(result, RosterUploadService)
