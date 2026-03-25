"""Tests for the core dependency injection factories."""

from unittest.mock import MagicMock

from learnwithai.di import (
    async_job_repo_factory,
    forbidden_job_queue_factory,
    membership_repo_factory,
    roster_upload_svc_factory,
    user_repo_factory,
)
from learnwithai.jobs.forbidden_job_queue import ForbiddenJobQueue
from learnwithai.repositories.async_job_repository import AsyncJobRepository
from learnwithai.repositories.membership_repository import MembershipRepository
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.services.roster_upload_service import RosterUploadService


def test_async_job_repo_factory() -> None:
    session = MagicMock()
    result = async_job_repo_factory(session)
    assert isinstance(result, AsyncJobRepository)


def test_user_repo_factory() -> None:
    session = MagicMock()
    result = user_repo_factory(session)
    assert isinstance(result, UserRepository)


def test_membership_repo_factory() -> None:
    session = MagicMock()
    result = membership_repo_factory(session)
    assert isinstance(result, MembershipRepository)


def test_forbidden_job_queue_factory() -> None:
    result = forbidden_job_queue_factory()
    assert isinstance(result, ForbiddenJobQueue)


def test_roster_upload_svc_factory() -> None:
    repo = MagicMock()
    user_repo = MagicMock()
    membership_repo = MagicMock()
    job_queue = MagicMock()
    result = roster_upload_svc_factory(repo, user_repo, membership_repo, job_queue)
    assert isinstance(result, RosterUploadService)
