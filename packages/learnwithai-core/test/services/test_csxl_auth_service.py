# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import jwt
import pytest
from learnwithai.config import Settings
from learnwithai.models.unc import UNCDirectorySearch
from learnwithai.repositories.user_repository import UserRepository
from learnwithai.services.csxl_auth_service import (
    AuthenticationException,
    CSXLAuthService,
)
from learnwithai.tables.user import User


def _build_service(
    settings: Settings | None = None,
    user_repo: UserRepository | None = None,
) -> CSXLAuthService:
    if settings is None:
        settings = Settings.model_construct(
            unc_auth_server_host="csxl.unc.edu",
            jwt_secret="really-secure-secret-is-really-secure",
            jwt_algorithm="HS256",
        )
    if user_repo is None:
        user_repo = MagicMock(spec=UserRepository)
    return CSXLAuthService(settings, user_repo)


def _make_user(**overrides) -> User:
    defaults = dict(
        pid=123456789,
        name="Test User",
        onyen="testuser",
    )
    defaults.update(overrides)
    return User.model_construct(_fields_set=None, **defaults)


# --- verify_auth_token ---


def test_verify_auth_token_returns_onyen_and_pid_on_success() -> None:
    # Arrange
    svc = _build_service()
    mock_response = httpx.Response(
        200,
        json={"uid": "testuser", "pid": "123456789"},
        request=httpx.Request("GET", "https://example.com"),
    )

    # Act
    with patch("learnwithai.services.csxl_auth_service.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__ = lambda s: s
        mock_client_cls.return_value.__exit__ = lambda s, *a: None
        mock_client_cls.return_value.get.return_value = mock_response
        onyen, pid = svc.verify_auth_token("valid-token")

    # Assert
    assert onyen == "testuser"
    assert pid == 123456789


def test_verify_auth_token_raises_on_non_200() -> None:
    # Arrange
    svc = _build_service()
    mock_response = httpx.Response(401, request=httpx.Request("GET", "https://example.com"))

    # Act / Assert
    with patch("learnwithai.services.csxl_auth_service.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__ = lambda s: s
        mock_client_cls.return_value.__exit__ = lambda s, *a: None
        mock_client_cls.return_value.get.return_value = mock_response
        with pytest.raises(AuthenticationException):
            svc.verify_auth_token("bad-token")


# --- registered_user_from_onyen_pid ---


def test_registered_user_from_onyen_pid_returns_existing_user() -> None:
    # Arrange
    existing_user = _make_user()
    user_repo = MagicMock(spec=UserRepository)
    user_repo.get_by_pid.return_value = existing_user
    svc = _build_service(user_repo=user_repo)

    # Act
    result = svc.registered_user_from_onyen_pid("testuser", 123456789)

    # Assert
    assert result is existing_user
    user_repo.get_by_pid.assert_called_once_with(123456789)


def test_registered_user_from_onyen_pid_registers_new_user_when_not_found() -> None:
    # Arrange
    new_user = _make_user()
    user_repo = MagicMock(spec=UserRepository)
    user_repo.get_by_pid.return_value = None
    user_repo.register_user.return_value = new_user
    svc = _build_service(user_repo=user_repo)

    directory_info = UNCDirectorySearch(
        pid="123456789",
        displayName="Test User",
        snIterator=["User"],
        givenNameIterator=["Test"],
        mailIterator=["test@example.com"],
    )

    # Act
    with patch.object(svc, "_unc_directory_lookup", return_value=directory_info):
        result = svc.registered_user_from_onyen_pid("testuser", 123456789)

    # Assert
    assert result is new_user
    user_repo.register_user.assert_called_once()
    registered = user_repo.register_user.call_args.args[0]
    assert registered.name == "Test User"
    assert registered.onyen == "testuser"
    assert registered.pid == 123456789
    assert registered.email == "test@example.com"
    assert registered.family_name == "User"
    assert registered.given_name == "Test"


# --- _unc_directory_lookup ---


def test_unc_directory_lookup_returns_parsed_result_on_success() -> None:
    # Arrange
    svc = _build_service()
    api_response = [
        {
            "displayName": "Test User",
            "snIterator": ["User"],
            "givenNameIterator": ["Test"],
            "mailIterator": ["test@example.com"],
        }
    ]
    mock_response = httpx.Response(200, json=api_response, request=httpx.Request("GET", "https://example.com"))

    # Act
    with patch("learnwithai.services.csxl_auth_service.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__ = lambda s: s
        mock_client_cls.return_value.__exit__ = lambda s, *a: None
        mock_client_cls.return_value.get.return_value = mock_response
        result = svc._unc_directory_lookup(123456789)

    # Assert
    assert result.pid == "123456789"
    assert result.displayName == "Test User"
    assert result.mailIterator == ["test@example.com"]


def test_unc_directory_lookup_returns_default_on_empty_results() -> None:
    # Arrange
    svc = _build_service()
    mock_response = httpx.Response(200, json=[], request=httpx.Request("GET", "https://example.com"))

    # Act
    with patch("learnwithai.services.csxl_auth_service.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__ = lambda s: s
        mock_client_cls.return_value.__exit__ = lambda s, *a: None
        mock_client_cls.return_value.get.return_value = mock_response
        result = svc._unc_directory_lookup(123456789)

    # Assert
    assert result.pid == "123456789"
    assert result.displayName == ""


def test_unc_directory_lookup_returns_default_on_non_200() -> None:
    # Arrange
    svc = _build_service()
    mock_response = httpx.Response(500, request=httpx.Request("GET", "https://example.com"))

    # Act
    with patch("learnwithai.services.csxl_auth_service.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__ = lambda s: s
        mock_client_cls.return_value.__exit__ = lambda s, *a: None
        mock_client_cls.return_value.get.return_value = mock_response
        result = svc._unc_directory_lookup(123456789)

    # Assert
    assert result.pid == "123456789"
    assert result.displayName == ""


# --- issue_jwt_token ---


def test_issue_jwt_token_returns_decodable_jwt() -> None:
    # Arrange
    user = _make_user()
    svc = _build_service()

    # Act
    token = svc.issue_jwt_token(user)

    # Assert
    decoded = jwt.decode(token, "really-secure-secret-is-really-secure", algorithms=["HS256"])
    assert decoded["sub"] == str(user.pid)
    assert "exp" in decoded


# --- verify_jwt ---


def test_verify_jwt_returns_pid_for_valid_token() -> None:
    # Arrange
    user = _make_user()
    svc = _build_service()
    token = svc.issue_jwt_token(user)

    # Act
    pid = svc.verify_jwt(token)

    # Assert
    assert pid == user.pid


def test_verify_jwt_raises_on_invalid_token() -> None:
    # Arrange
    svc = _build_service()

    # Act / Assert
    with pytest.raises(AuthenticationException):
        svc.verify_jwt("invalid-token")


def test_verify_jwt_raises_on_expired_token() -> None:
    # Arrange
    svc = _build_service()
    expired_payload = {"sub": "123456789", "exp": 0}
    expired_token = jwt.encode(
        expired_payload,
        "really-secure-secret-is-really-secure",
        algorithm="HS256",
    )

    # Act / Assert
    with pytest.raises(AuthenticationException):
        svc.verify_jwt(expired_token)


# --- get_user_by_pid ---


def test_get_user_by_pid_delegates_to_repository() -> None:
    # Arrange
    user = _make_user()
    user_repo = MagicMock(spec=UserRepository)
    user_repo.get_by_pid.return_value = user
    svc = _build_service(user_repo=user_repo)

    # Act
    result = svc.get_user_by_pid(user.pid)

    # Assert
    assert result is user
    user_repo.get_by_pid.assert_called_once_with(user.pid)


def test_get_user_by_pid_returns_none_when_not_found() -> None:
    # Arrange
    user_repo = MagicMock(spec=UserRepository)
    user_repo.get_by_pid.return_value = None
    svc = _build_service(user_repo=user_repo)

    # Act
    result = svc.get_user_by_pid(999999999)

    # Assert
    assert result is None
