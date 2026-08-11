# Docker

Packages the backend as a self-contained, locally-runnable image (hosted or
air-gapped), optionally serving the static SPA from the same container. The core
calculation makes **no external runtime calls** — it serves purely from the
version-controlled presets baked into the image.

## Files

- `Dockerfile` — backend image. Multi-stage build (uv). The engine + API are
  installed non-editably into a self-contained venv, so the runtime image carries
  no source tree and no dev tooling. Runs as a non-root user with a `/v1/health`
  healthcheck.
- `docker-compose.yml` — full-stack local run: `backend` + `frontend` services.
- The frontend image is defined next to the SPA in [`../web/Dockerfile`](../web/Dockerfile)
  (with its own `nginx.conf`): a Node build stage runs `npm run build`, and nginx
  serves the static bundle while reverse-proxying `/v1/*` to the `backend` service.
  Serving both through one origin means the SPA needs no CORS config.

## Build & run

### Full stack (backend + frontend)

```sh
make docker-up          # builds both images and runs the stack
# equivalent to:
docker compose -f docker/docker-compose.yml up --build
```

Then open the SPA at **http://localhost:8360** — nginx proxies its API calls to the
backend, so it's a single origin. The API is also exposed directly on
**http://localhost:8350** for the CLI:

```sh
vllm-calc check --api-url http://localhost:8350 --model llama-3.3-70b --gpu a100-80gb:2 --tp 2
```

Tear it down with `make docker-down`.

If either host port (`8360` or `8350`) is already taken on your machine, edit the
host side of the relevant `ports:` mapping in `docker-compose.yml` (e.g. `"8360:80"`
→ `"8399:80"`) — the container-internal port after the colon must stay unchanged.

### Backend image only

```sh
# From the repo root (build context = repo root):
docker build -f docker/Dockerfile -t vllm-calc-backend .
docker run --rm -p 8350:8000 vllm-calc-backend
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
