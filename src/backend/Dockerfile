# syntax=docker/dockerfile:1.7

# -----------------------------------------------------------------------------
# Base image for ALL stages
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
    PIP_NO_BINARY="nvidia*,cuda*,cudnn*,cublas*" \
    PIP_PREFER_BINARY=1 \
    PIP_ONLY_BINARY=":all:"

WORKDIR /app


# -----------------------------------------------------------------------------
# Builder stage – build an isolated venv with all runtime deps
# -----------------------------------------------------------------------------
FROM base AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade core tooling
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel pip-tools

# Install CPU-only torch first
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --extra-index-url https://download.pytorch.org/whl/cpu torch==2.2.1+cpu

COPY pyproject.toml ./pyproject.toml

# Generate lockfile inside Python 3.12 env
RUN --mount=type=cache,target=/root/.cache/pip \
    pip-compile --resolver=backtracking --quiet pyproject.toml -o requirements.lock

# Install FULL dependency set from lockfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.lock && \
    pip install uvloop

# -----------------------------------------------------------------------------
# Runtime stage – clean, minimal image using the built venv
# -----------------------------------------------------------------------------
FROM base AS runtime

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/scripts && chown -R appuser:appuser /app

# Copy application code and scripts
COPY --chown=appuser:appuser swx_api ./swx_api
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser scripts /app/scripts/
COPY --chown=appuser:appuser pyproject.toml ./pyproject.toml
COPY --chown=appuser:appuser --from=builder /app/requirements.lock /app/requirements.lock

RUN chmod +x /app/scripts/docker-entrypoint.sh \
    /app/scripts/rollback_last_migration.sh \
    /app/scripts/check_schema_diff.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://127.0.0.1:8000/healthz', timeout=5)" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/scripts/docker-entrypoint.sh"]

CMD ["gunicorn", \
     "swx_api.core.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--threads", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "90", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
