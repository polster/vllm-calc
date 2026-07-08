"""FastAPI application factory and versioned meta endpoints."""

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

import vllm_calc_engine

# The vLLM version range this engine's estimates are calibrated for. Surfaced so
# results are honestly labeled (NFR16); refined by the validation harness (Epic 4).
SUPPORTED_VLLM_RANGE = ">=0.13,<0.14"

v1 = APIRouter(prefix="/v1")


class Health(BaseModel):
    status: str


class Version(BaseModel):
    engine_version: str
    supported_vllm_range: str


@v1.get("/health")
def health() -> Health:
    return Health(status="ok")


@v1.get("/version")
def version() -> Version:
    return Version(
        engine_version=vllm_calc_engine.__version__,
        supported_vllm_range=SUPPORTED_VLLM_RANGE,
    )


def create_app() -> FastAPI:
    app = FastAPI(title="vllm-calc", version=vllm_calc_engine.__version__)
    app.include_router(v1)
    return app


app = create_app()
