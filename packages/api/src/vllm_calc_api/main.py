"""FastAPI application factory.

Thin HTTP layer over the engine. Owns no calculation logic (parity invariant).
Presets are loaded and validated once at startup (fail-fast); all business routes
live under the versioned /v1 prefix. Operational behaviour (CORS, rate limiting,
optional bundled SPA) is env-driven so one image runs hosted or air-gapped.
"""

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import vllm_calc_engine
from vllm_calc_api import settings
from vllm_calc_api.errors import register_exception_handlers
from vllm_calc_api.presets_loader import load_gpu_presets, load_model_presets
from vllm_calc_api.routes import calculate, meta, presets, validation

__all__ = ["create_app"]


def create_app() -> FastAPI:
    app = FastAPI(title="vllm-calc", version=vllm_calc_engine.__version__)

    # Load + validate presets once at startup (fail-fast on a bad preset).
    base = settings.presets_dir()
    app.state.model_presets = load_model_presets(base / "models")
    app.state.gpu_presets = load_gpu_presets(base / "gpus")

    origins = settings.cors_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    if settings.rate_limit_enabled():
        _install_rate_limit(app, settings.rate_limit_per_minute())

    register_exception_handlers(app)
    for router in (meta.router, calculate.router, presets.router, validation.router):
        app.include_router(router, prefix="/v1")

    # Optionally serve the built SPA from the same container (mounted last so the
    # /v1 API routes take precedence).
    spa = settings.spa_dir()
    if spa is not None:
        app.mount("/", StaticFiles(directory=spa, html=True), name="spa")

    return app


def _install_rate_limit(app: FastAPI, per_minute: int) -> None:
    """A minimal per-client fixed-window limiter (in-process; NFR13 hardening).

    Sufficient for a single stateless instance; a shared store would be needed to
    limit across horizontally-scaled replicas.
    """
    hits: dict[str, list[float]] = {}
    last_sweep = 0.0

    @app.middleware("http")
    async def _rate_limit(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        nonlocal last_sweep
        client = request.client.host if request.client else "anonymous"
        now = time.monotonic()
        # Periodic sweep so idle clients' entries can't accumulate unbounded (a
        # unique-IP spray would otherwise be a memory-exhaustion vector).
        if now - last_sweep > 60.0:
            for stale in [k for k, ts in hits.items() if all(now - t >= 60.0 for t in ts)]:
                del hits[stale]
            last_sweep = now
        recent = [t for t in hits.get(client, []) if now - t < 60.0]
        if len(recent) >= per_minute:
            hits[client] = recent
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "type": "rate_limited",
                        "message": "Too many requests.",
                        "details": None,
                    }
                },
            )
        recent.append(now)
        hits[client] = recent
        return await call_next(request)


app = create_app()
