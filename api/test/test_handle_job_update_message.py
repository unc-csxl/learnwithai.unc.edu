"""Tests for the _handle_job_update_message helper in main.py."""

from __future__ import annotations

import asyncio
import json

import pytest
from unittest.mock import AsyncMock

from api.job_update_manager import JobUpdateManager
from api.main import _handle_job_update_message


def _valid_body() -> bytes:
    return json.dumps(
        {"job_id": 1, "course_id": 10, "kind": "test", "status": "completed"}
    ).encode()


class TestHandleJobUpdateMessage:
    def test_parses_and_broadcasts_valid_message(self) -> None:
        manager = JobUpdateManager()
        manager.broadcast = AsyncMock()  # type: ignore[method-assign]

        asyncio.run(_handle_job_update_message(manager, _valid_body()))

        manager.broadcast.assert_called_once()
        update = manager.broadcast.call_args[0][0]
        assert update.job_id == 1
        assert update.course_id == 10
        assert update.kind == "test"
        assert update.status == "completed"

    def test_raises_on_invalid_json(self) -> None:
        manager = JobUpdateManager()

        with pytest.raises(Exception):
            asyncio.run(_handle_job_update_message(manager, b"not json"))

    def test_raises_on_missing_fields(self) -> None:
        manager = JobUpdateManager()
        body = json.dumps({"job_id": 1}).encode()

        with pytest.raises(Exception):
            asyncio.run(_handle_job_update_message(manager, body))
