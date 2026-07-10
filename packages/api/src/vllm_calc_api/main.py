"""FastAPI application factory.

Thin HTTP layer over the engine. Owns no calculation logic (parity invariant).
Presets are loaded and validated once at startup (fail-fast); all business routes
live under the versioned /v1 prefix.
"""

from fastapi import FastAPI

import vllm_calc_engine
from vllm_calc_api import settings
from vllm_calc_api.errors import register_exception_handlers
from vllm_calc_api.presets_loader import load_gpu_presets, load_model_presets
from vllm_calc_api.routes import calculate, meta, presets

__all__ = ["create_app"]


def create_app() -> FastAPI:
    app = FastAPI(title="vllm-calc", version=vllm_calc_engine.__version__)

    # Load + validate presets once at startup (fail-fast on a bad preset).
    base = settings.presets_dir()
    app.state.model_presets = load_model_presets(base / "models")
    app.state.gpu_presets = load_gpu_presets(base / "gpus")

    register_exception_handlers(app)
    for router in (meta.router, calculate.router, presets.router):
        app.include_router(router, prefix="/v1")
    return app


app = create_app()
