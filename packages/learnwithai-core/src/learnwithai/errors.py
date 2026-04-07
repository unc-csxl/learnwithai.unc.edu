# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Application-specific exceptions for learnwithai-core."""


class AuthorizationError(Exception):
    """Raised when a user lacks permission for the requested operation."""
