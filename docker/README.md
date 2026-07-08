# Docker

Packages the backend as a self-contained, locally-runnable image (hosted or
air-gapped), optionally serving the static SPA from the same container.

- `Dockerfile` — backend image (+ optional bundled SPA)
- `docker-compose.yml` — local run convenience

Implemented in **Story 3.2**. Runtime config is via environment variables
(API base URL, pinned vLLM version, CORS origins, rate-limit toggle); no external
runtime calls are required for the core calculation.
