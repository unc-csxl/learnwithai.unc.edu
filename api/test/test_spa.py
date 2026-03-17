from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.spa import guess_media_type, mount_spa, resolve_static_dir
from learnwithai.config import Settings


# ---- resolve_static_dir ----


def test_resolve_static_dir_uses_setting_when_provided() -> None:
    settings = Settings.model_construct(static_dir="/custom/path")
    assert resolve_static_dir(settings) == Path("/custom/path")


def test_resolve_static_dir_falls_back_when_empty() -> None:
    settings = Settings.model_construct(static_dir="")
    result = resolve_static_dir(settings)
    # Should resolve to a path ending with "static" relative to the package
    assert result.name == "static"


# ---- guess_media_type ----


@pytest.mark.parametrize(
    ("suffix", "expected"),
    [
        (".js", "application/javascript"),
        (".css", "text/css"),
        (".html", "text/html"),
        (".json", "application/json"),
        (".ico", "image/x-icon"),
        (".svg", "image/svg+xml"),
        (".png", "image/png"),
        (".jpg", "image/jpeg"),
        (".woff2", "font/woff2"),
        (".woff", "font/woff"),
        (".txt", "text/plain"),
        (".xyz", "application/octet-stream"),
    ],
)
def test_guess_media_type_returns_expected_type(suffix: str, expected: str) -> None:
    assert guess_media_type(Path(f"file{suffix}")) == expected


# ---- mount_spa ----


@pytest.fixture
def spa_app(tmp_path: Path) -> tuple[TestClient, Path]:
    """Creates a FastAPI app with SPA serving mounted on a temporary directory."""
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>SPA</body></html>")
    (static_dir / "main.js").write_text("console.log('hello')")
    (static_dir / "styles.css").write_text("body { margin: 0; }")

    application = FastAPI()

    @application.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    mount_spa(application, static_dir)
    return TestClient(application), static_dir


@pytest.mark.integration
def test_spa_serves_index_for_unknown_paths(
    spa_app: tuple[TestClient, Path],
) -> None:
    client, _ = spa_app
    response = client.get("/some/angular/route")
    assert response.status_code == 200
    assert "SPA" in response.text


@pytest.mark.integration
def test_spa_serves_static_file_directly(
    spa_app: tuple[TestClient, Path],
) -> None:
    client, _ = spa_app
    response = client.get("/main.js")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/javascript"
    assert "hello" in response.text


@pytest.mark.integration
def test_spa_preserves_api_routes(
    spa_app: tuple[TestClient, Path],
) -> None:
    client, _ = spa_app
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_spa_returns_404_for_unmatched_api_paths(
    spa_app: tuple[TestClient, Path],
) -> None:
    client, _ = spa_app
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
