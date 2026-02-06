# syntax=docker/dockerfile:1

# Build stage - install dependencies with uv
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.31 /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (production only, no dev dependencies)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini ./

# Install the project itself
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Security: non-root user
RUN addgroup --gid 10001 appgroup && \
    adduser --uid 10001 --gid 10001 --disabled-password --gecos "" appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application code
COPY --from=builder --chown=appuser:appgroup /app/src /app/src
COPY --from=builder --chown=appuser:appgroup /app/fixtures /app/fixtures
COPY --from=builder --chown=appuser:appgroup /app/scripts /app/scripts
COPY --from=builder --chown=appuser:appgroup /app/alembic /app/alembic
COPY --from=builder --chown=appuser:appgroup /app/alembic.ini /app/alembic.ini

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run uses PORT env var (defaults to 8080)
ENV PORT=8080

USER appuser

EXPOSE 8080

# Run with uvicorn directly for Cloud Run (proper signal handling via SIGTERM)
# For local dev with docker-compose, override with entrypoint.sh
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
