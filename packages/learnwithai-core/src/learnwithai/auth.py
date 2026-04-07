# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Lightweight JWT verification for use across HTTP and WebSocket layers."""

import jwt

from .config import Settings
from .services.csxl_auth_service import AuthenticationException


def verify_jwt(token: str, settings: Settings) -> int:
    """Decodes a JWT and returns the user PID.

    This is the canonical JWT verification function. Both the HTTP
    authentication dependency and the WebSocket endpoint delegate here.

    Args:
        token: Encoded JWT issued by :class:`CSXLAuthService`.
        settings: Application settings containing the JWT secret and algorithm.

    Returns:
        The user PID stored in the token ``sub`` claim.

    Raises:
        AuthenticationException: If the token is invalid, expired, or
            missing the expected claims.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AuthenticationException() from exc
