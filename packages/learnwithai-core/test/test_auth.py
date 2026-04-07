# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Tests for the standalone verify_jwt function."""

import jwt
import pytest
from learnwithai.auth import verify_jwt
from learnwithai.config import Settings
from learnwithai.services.csxl_auth_service import AuthenticationException

_SETTINGS = Settings(
    jwt_secret="really-secure-secret-is-really-secure",
    jwt_algorithm="HS256",
)


def _encode(payload: dict) -> str:
    return jwt.encode(payload, _SETTINGS.jwt_secret, algorithm=_SETTINGS.jwt_algorithm)


def test_returns_pid_for_valid_token() -> None:
    token = _encode({"sub": "730123456", "exp": 9999999999})
    assert verify_jwt(token, _SETTINGS) == 730123456


def test_raises_on_invalid_token() -> None:
    with pytest.raises(AuthenticationException):
        verify_jwt("not-a-token", _SETTINGS)


def test_raises_on_expired_token() -> None:
    token = _encode({"sub": "123", "exp": 0})
    with pytest.raises(AuthenticationException):
        verify_jwt(token, _SETTINGS)


def test_raises_when_sub_claim_missing() -> None:
    token = _encode({"exp": 9999999999})
    with pytest.raises(AuthenticationException):
        verify_jwt(token, _SETTINGS)
