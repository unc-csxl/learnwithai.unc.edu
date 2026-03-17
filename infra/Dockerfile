# -----------------------------------------------------------------------------
# Stage 1 – Build Angular frontend
# -----------------------------------------------------------------------------
FROM node:24-slim AS frontend-build

RUN corepack enable && corepack prepare pnpm@10.32.1 --activate

WORKDIR /build/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm build

# -----------------------------------------------------------------------------
# Stage 2 – Production Python image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create a non-root user
RUN groupadd --gid 1001 app && useradd --uid 1001 --gid app --create-home app

WORKDIR /app

# Copy Python workspace files needed for dependency resolution
COPY pyproject.toml uv.lock ./
COPY api/ api/
COPY packages/ packages/

# Install production dependencies only (no dev/test extras)
RUN uv sync --all-packages --no-dev --no-editable \
    && rm -rf /root/.cache

# Copy the built Angular assets into the location FastAPI expects
COPY --from=frontend-build /build/frontend/dist/learnwithai/browser/ /app/static/

# Switch to non-root user
USER app

ENV ENVIRONMENT=production \
    PATH=/app/.venv/bin:$PATH \
    STATIC_DIR=/app/static \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Default command: run the API server
CMD ["/app/.venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
