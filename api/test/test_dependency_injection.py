from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.dependency_injection import (
    get_course_by_path_id,
    get_user_by_add_member_request_pid,
    get_user_by_pid,
)
from api.models import AddMemberRequest
from learnwithai.tables.membership import MembershipType


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


def test_get_user_by_add_member_request_pid_returns_user() -> None:
    # Arrange
    user = MagicMock()
    user_repo = MagicMock()
    user_repo.get_by_pid.return_value = user
    body = AddMemberRequest(pid=123, type=MembershipType.STUDENT)

    # Act
    result = get_user_by_add_member_request_pid(body, user_repo)

    # Assert
    assert result is user
    user_repo.get_by_pid.assert_called_once_with(123)
