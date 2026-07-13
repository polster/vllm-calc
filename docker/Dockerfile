# syntax=docker/dockerfile:1
#
# Self-contained backend image for vllm-calc. Builds the engine + API into a
# non-editable venv so the runtime needs no source tree, and serves purely from
# local data — no external runtime calls (air-gapped-capable, NFR8).
#
# Build from the repo root:  docker build -f docker/Dockerfile -t vllm-calc-backend .

FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

# Workspace manifests + sources needed to resolve and build the packages.
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/

# Install ONLY the API (+ its engine dep) into /app/.venv as real wheels (no editable
# installs), excluding dev tooling. Scoping to the api package keeps the cli and the
# GPU validation harness out of the runtime image. --frozen fails if the lock is stale.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package vllm-calc-api


FROM python:3.13-slim-bookworm AS runtime
WORKDIR /app

# The self-contained venv and the version-controlled presets are all the runtime needs.
COPY --from=builder /app/.venv /app/.venv
COPY presets/ /app/presets/

ENV PATH="/app/.venv/bin:$PATH" \
    VLLM_CALC_PRESETS_DIR=/app/presets \
    PORT=8000
# Operational config (all optional; documented in docker/README.md):
#   CORS_ORIGINS, RATE_LIMIT_ENABLED, RATE_LIMIT_PER_MINUTE, VLLM_VERSION_RANGE, SPA_DIR

RUN useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/v1/health')" || exit 1

CMD ["sh", "-c", "uvicorn vllm_calc_api.main:app --host 0.0.0.0 --port ${PORT}"]
