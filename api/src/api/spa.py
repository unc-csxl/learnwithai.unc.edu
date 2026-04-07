# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

"""Single-page application static file serving helpers."""

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from learnwithai.config import Settings

_MEDIA_TYPES: dict[str, str] = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".html": "text/html",
    ".json": "application/json",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".txt": "text/plain",
}


def resolve_static_dir(settings: Settings) -> Path:
    """Returns the static directory from settings or a sensible default."""
    if settings.static_dir:
        return Path(settings.static_dir)
    return Path(__file__).resolve().parent.parent.parent / "static"


def guess_media_type(path: Path) -> str:
    """Returns a MIME type for common static asset extensions."""
    return _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")


def mount_spa(application: FastAPI, static_dir: Path) -> None:
    """Mounts static file serving and an SPA catch-all on the application."""
    static_root = static_dir.resolve()

    @application.get("/api/{rest_of_path:path}", status_code=404, include_in_schema=False)
    def api_fallback() -> dict[str, str]:
        """Returns 404 for unmatched API paths while SPA routing is enabled."""
        return {"detail": "Not Found"}

    application.mount("/assets", StaticFiles(directory=static_dir), name="static-assets")

    @application.get("/{full_path:path}", include_in_schema=False)
    def serve_spa_route(request: Request) -> Response:
        """Serves the Angular application for non-API and non-asset paths."""
        requested_path = (static_root / request.path_params["full_path"]).resolve()
        if requested_path.is_file() and requested_path.is_relative_to(static_root):
            return Response(
                content=requested_path.read_bytes(),
                media_type=guess_media_type(requested_path),
            )

        index = static_root / "index.html"
        return HTMLResponse(content=index.read_text())


def configure_spa(application: FastAPI, settings: Settings) -> None:
    """Enables SPA/static file serving when running in production."""
    static_dir = resolve_static_dir(settings)
    if settings.is_production and static_dir.is_dir():
        mount_spa(application, static_dir)  # pragma: no cover
