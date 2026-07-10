"""Meta endpoints: health and version."""

from fastapi import APIRouter
from pydantic import BaseModel

import vllm_calc_engine
from vllm_calc_api import settings

router = APIRouter(tags=["meta"])


class Health(BaseModel):
    status: str


class Version(BaseModel):
    engine_version: str
    supported_vllm_range: str


@router.get("/health")
def health() -> Health:
    return Health(status="ok")


@router.get("/version")
def version() -> Version:
    return Version(
        engine_version=vllm_calc_engine.__version__,
        supported_vllm_range=settings.vllm_version_range(),
    )
