# Docker

Packages the backend as a self-contained, locally-runnable image (hosted or
air-gapped), optionally serving the static SPA from the same container. The core
calculation makes **no external runtime calls** — it serves purely from the
version-controlled presets baked into the image.

## Files

- `Dockerfile` — multi-stage build (uv). The engine + API are installed
  non-editably into a self-contained venv, so the runtime image carries no source
  tree and no dev tooling. Runs as a non-root user with a `/v1/health` healthcheck.
- `docker-compose.yml` — local run convenience.

## Build & run

```sh
# From the repo root (build context = repo root):
docker build -f docker/Dockerfile -t vllm-calc-backend .
docker run --rm -p 8000:8000 vllm-calc-backend

# or:
docker compose -f docker/docker-compose.yml up --build
```

Then point either surface at it:

```sh
# SPA
VITE_API_BASE_URL=http://localhost:8000 npm --prefix web run dev
# CLI
vllm-calc check --api-url http://localhost:8000 --model llama-3.3-70b --gpu a100-80gb:2 --tp 2
```

## Configuration (all via environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `VLLM_CALC_PRESETS_DIR` | `/app/presets` | Where model/GPU preset YAML is read from. |
| `CORS_ORIGINS` | _(none)_ | Comma-separated allowed origins for a separately-hosted SPA. Empty = same-origin only. |
| `RATE_LIMIT_ENABLED` | `false` | Turn on the per-client fixed-window rate limiter. |
| `RATE_LIMIT_PER_MINUTE` | `120` | Requests/minute/client when rate limiting is on. |
| `VLLM_VERSION_RANGE` | engine default | Overrides the calibrated vLLM range reported by `/v1/version`. |
| `SPA_DIR` | _(none)_ | If set to a directory of built SPA assets, serves them at `/` from the same container. |
| `PORT` | `8000` | Port uvicorn binds. |

No variable is required — an unconfigured container serves calculations offline.
