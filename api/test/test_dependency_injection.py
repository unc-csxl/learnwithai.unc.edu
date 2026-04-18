# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.di import (
    activity_repository_factory,
    activity_service_factory,
    async_job_repository_factory,
    course_repository_factory,
    get_activity_by_path_id,
    get_course_by_path_id,
    get_user_by_pid,
    iyow_activity_repository_factory,
    iyow_activity_service_factory,
    iyow_submission_repository_factory,
    iyow_submission_service_factory,
    job_control_service_factory,
    joke_generation_service_factory,
    joke_repository_factory,
    metrics_service_factory,
    operator_repository_factory,
    operator_service_factory,
    roster_upload_service_factory,
    submission_repository_factory,
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

    result = roster_upload_service_factory(async_job_repo, user_repo, membership_repo, job_queue)

    assert isinstance(result, RosterUploadService)


def test_joke_generation_service_factory_returns_service() -> None:
    from learnwithai.tools.jokes.service import JokeGenerationService

    joke_repo = MagicMock()
    async_job_repo = MagicMock()
    job_queue = MagicMock()

    result = joke_generation_service_factory(joke_repo, async_job_repo, job_queue)

    assert isinstance(result, JokeGenerationService)


def test_joke_repository_factory_returns_repository() -> None:
    from learnwithai.tools.jokes.repository import JokeRepository

    session = MagicMock()

    result = joke_repository_factory(session)

    assert isinstance(result, JokeRepository)


def test_activity_repository_factory_returns_repository() -> None:
    from learnwithai.repositories.activity_repository import ActivityRepository

    session = MagicMock()

    result = activity_repository_factory(session)

    assert isinstance(result, ActivityRepository)


def test_submission_repository_factory_returns_repository() -> None:
    from learnwithai.repositories.submission_repository import SubmissionRepository

    session = MagicMock()

    result = submission_repository_factory(session)

    assert isinstance(result, SubmissionRepository)


def test_iyow_activity_repository_factory_returns_repository() -> None:
    from learnwithai.activities.iyow.repository import IyowActivityRepository

    session = MagicMock()

    result = iyow_activity_repository_factory(session)

    assert isinstance(result, IyowActivityRepository)


def test_iyow_submission_repository_factory_returns_repository() -> None:
    from learnwithai.activities.iyow.repository import IyowSubmissionRepository

    session = MagicMock()

    result = iyow_submission_repository_factory(session)

    assert isinstance(result, IyowSubmissionRepository)


def test_activity_service_factory_returns_service() -> None:
    from learnwithai.services.activity_service import ActivityService

    activity_repo = MagicMock()
    membership_repo = MagicMock()

    result = activity_service_factory(activity_repo, membership_repo)

    assert isinstance(result, ActivityService)


def test_iyow_activity_service_factory_returns_service() -> None:
    from learnwithai.activities.iyow.service import IyowActivityService

    activity_svc = MagicMock()
    iyow_activity_repo = MagicMock()

    result = iyow_activity_service_factory(activity_svc, iyow_activity_repo)

    assert isinstance(result, IyowActivityService)


def test_iyow_submission_service_factory_returns_service() -> None:
    from learnwithai.activities.iyow.submission_service import IyowSubmissionService

    result = iyow_submission_service_factory(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())

    assert isinstance(result, IyowSubmissionService)


def test_get_activity_by_path_id_returns_activity() -> None:
    activity = MagicMock()
    activity_repo = MagicMock()
    activity_repo.get_by_id.return_value = activity

    result = get_activity_by_path_id(10, activity_repo)

    assert result is activity
    activity_repo.get_by_id.assert_called_once_with(10)


def test_get_activity_by_path_id_raises_for_missing_activity() -> None:
    activity_repo = MagicMock()
    activity_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_activity_by_path_id(10, activity_repo)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Activity not found."


def test_operator_repository_factory_returns_repository() -> None:
    from learnwithai.repositories.operator_repository import OperatorRepository

    session = MagicMock()

    result = operator_repository_factory(session)

    assert isinstance(result, OperatorRepository)


def test_operator_service_factory_returns_service() -> None:
    from learnwithai.services.operator_service import OperatorService

    operator_repo = MagicMock()
    user_repo = MagicMock()

    result = operator_service_factory(operator_repo, user_repo)

    assert isinstance(result, OperatorService)


def test_metrics_service_factory_returns_service() -> None:
    from learnwithai.services.metrics_service import MetricsService

    session = MagicMock()
    operator_svc = MagicMock()

    result = metrics_service_factory(session, operator_svc)

    assert isinstance(result, MetricsService)


def test_job_control_service_factory_returns_service() -> None:
    from learnwithai.services.job_control_service import JobControlService

    session = MagicMock()
    operator_svc = MagicMock()
    settings = MagicMock()
    settings.effective_rabbitmq_management_url = "http://rabbitmq:15672"
    settings.effective_rabbitmq_management_user = "guest"
    settings.effective_rabbitmq_management_password = "guest"

    result = job_control_service_factory(session, operator_svc, settings)

    assert isinstance(result, JobControlService)
