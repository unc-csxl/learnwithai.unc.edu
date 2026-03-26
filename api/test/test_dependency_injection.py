from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.di import (
    async_job_repository_factory,
    course_repository_factory,
    get_course_by_path_id,
    get_user_by_pid,
    roster_upload_service_factory,
)


def test_get_course_by_path_id_returns_course() -> None:
    # Arrange
    course = MagicMock()
    course_repo = MagicMock()
    course_repo.get_by_id.return_value = course

    # Act
    result = get_course_by_path_id(1, course_repo)

    # Assert
    assert result is course
    course_repo.get_by_id.assert_called_once_with(1)


def test_get_course_by_path_id_raises_for_missing_course() -> None:
    # Arrange
    course_repo = MagicMock()
    course_repo.get_by_id.return_value = None

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        get_course_by_path_id(1, course_repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Course not found."


def test_get_user_by_pid_returns_user() -> None:
    # Arrange
    user = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = user

    # Act
    result = get_user_by_pid(123, user_repo)

    # Assert
    assert result is user
    user_repo.get_by_pid.assert_called_once_with(123)


def test_get_user_by_pid_raises_for_missing_user() -> None:
    # Arrange
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = None

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        get_user_by_pid(123, user_repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found."


def test_course_repository_factory_returns_repository() -> None:
    from learnwithai.repositories.course_repository import CourseRepository

    session = MagicMock()

    result = course_repository_factory(session)

    assert isinstance(result, CourseRepository)


def test_async_job_repository_factory_returns_repository() -> None:
    from learnwithai.repositories.async_job_repository import AsyncJobRepository

    session = MagicMock()

    result = async_job_repository_factory(session)

    assert isinstance(result, AsyncJobRepository)


def test_roster_upload_service_factory_returns_service() -> None:
    from learnwithai.services.roster_upload_service import RosterUploadService

    async_job_repo = MagicMock()
    user_repo = MagicMock()
    membership_repo = MagicMock()
    job_queue = MagicMock()

    result = roster_upload_service_factory(
        async_job_repo, user_repo, membership_repo, job_queue
    )

    assert isinstance(result, RosterUploadService)
