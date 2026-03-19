"""Tests for the database reset script."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch


def _load_reset_module() -> ModuleType:
    """Load the reset_database.py script as a module."""
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "reset_database.py"
    )
    spec = importlib.util.spec_from_file_location("reset_database", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Expected reset_database script to be loadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_resets_database_and_seeds(monkeypatch) -> None:
    module = _load_reset_module()

    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(
            module,
            "Settings",
            return_value=MagicMock(environment="development"),
        ),
        patch.object(module, "reset_db_and_tables") as mock_reset,
        patch.object(module, "Session", return_value=mock_session) as mock_session_cls,
        patch.object(module, "get_engine") as mock_engine,
        patch.object(module, "seed") as mock_seed,
        patch("builtins.print"),
    ):
        module.main()

    mock_reset.assert_called_once()
    mock_seed.assert_called_once_with(mock_session)
    mock_session.commit.assert_called_once()


def test_main_exits_in_non_development_environment() -> None:
    module = _load_reset_module()

    with (
        patch.object(
            module,
            "Settings",
            return_value=MagicMock(environment="production"),
        ),
        patch("builtins.print"),
    ):
        try:
            module.main()
            assert False, "Expected SystemExit"
        except SystemExit as exc:
            assert exc.code == 1
