# Stage 1: build the venv with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Install dependencies first (layer cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Install the project itself
COPY README.md ./
COPY src/ src/
RUN uv sync --frozen --no-dev


# Stage 2: final runtime image
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Copy the pre-built venv
COPY --from=builder /app/.venv /app/.venv

# Copy application source and alembic migrations
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn squola.main:app --host 0.0.0.0 --port 8000"]
