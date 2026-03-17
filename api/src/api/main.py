"""Application entrypoint for the FastAPI adapter."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routes.health import router as health_router
from api.routes.auth import router as auth_router

from learnwithai.config import Settings


def _resolve_static_dir(settings: Settings) -> Path:
    """Returns the static directory from settings or a sensible default."""
    if settings.static_dir:
        return Path(settings.static_dir)
    # Fallback: look relative to the repository root (works in dev layouts)
    return Path(__file__).resolve().parent.parent.parent / "static"

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


def guess_media_type(path: Path) -> str:
    """Returns a MIME type for common static asset extensions."""
    return _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")


def mount_spa(application: FastAPI, static_dir: Path) -> None:
    """Mounts static file serving and an SPA catch-all on *application*.

    This is called in production so that FastAPI serves the pre-built Angular
    assets alongside the API routes from a single container.
    """

    @application.get("/api/{rest_of_path:path}", status_code=404)
    def api_fallback() -> dict:
        """Returns 404 for unmatched ``/api`` paths."""
        return {"detail": "Not Found"}

    application.mount(
        "/assets", StaticFiles(directory=static_dir), name="static-assets"
    )

    @application.get("/{full_path:path}")
    def serve_spa_route(request: Request) -> HTMLResponse:
        """Serves the Angular application for any non-API, non-asset path."""
        file_path = static_dir / request.path_params["full_path"]
        if file_path.is_file():
            return HTMLResponse(
                content=file_path.read_bytes(),
                media_type=guess_media_type(file_path),
            )
        index = static_dir / "index.html"
        return HTMLResponse(content=index.read_text())


settings = Settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")

static_dir = _resolve_static_dir(settings)
if settings.is_production and static_dir.is_dir():
    mount_spa(app, static_dir)
