"""Export the OpenAPI specification to frontend/openapi.json.

Usage::

    uv run python scripts/export_openapi.py

The script imports the FastAPI application, serialises its OpenAPI schema,
and writes it to ``frontend/openapi.json``.  Frontend developers can then
run ``pnpm api:gen`` to regenerate the TypeScript client without needing a
running API server.
"""

import json
import pathlib

from api.main import app


def main() -> None:
    """Dump the current OpenAPI specification to disk."""
    spec = app.openapi()
    out = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "openapi.json"
    out.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
