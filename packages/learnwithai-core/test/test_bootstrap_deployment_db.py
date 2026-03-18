from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock
from unittest.mock import patch


def load_bootstrap_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_deployment_db.py"
    )
    spec = importlib.util.spec_from_file_location(
        "bootstrap_deployment_db", script_path
    )
    if spec is None or spec.loader is None:
        raise AssertionError("Expected bootstrap deployment script to be loadable")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_creates_tables_and_seeds_demo_user() -> None:
    module = load_bootstrap_module()
    session = MagicMock()
    session_context = MagicMock()
    session_context.__enter__.return_value = session
    expected_user = {
        "name": "Demo User",
        "pid": 999999999,
        "onyen": "demo",
        "family_name": "User",
        "given_name": "Demo",
        "email": "demo@example.com",
    }

    with (
        patch.object(module, "create_db_and_tables") as create_db_and_tables_mock,
        patch.object(module, "get_session", return_value=session_context),
        patch.object(module, "User", side_effect=lambda **kwargs: kwargs) as user_mock,
        patch("builtins.print") as print_mock,
    ):
        module.main()

    create_db_and_tables_mock.assert_called_once_with()
    user_mock.assert_called_once_with(**expected_user)
    session.add.assert_called_once_with(expected_user)
    session.commit.assert_called_once_with()
    print_mock.assert_called_once_with("Created tables and dummy user.")
