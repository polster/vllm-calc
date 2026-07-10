"""Preset listing endpoints. Presets are loaded once at startup into app state."""

from fastapi import APIRouter, Request

from vllm_calc_engine.models import GpuPreset, ModelPreset

router = APIRouter(tags=["presets"])


@router.get("/presets/models", response_model=list[ModelPreset])
def list_model_presets(request: Request) -> list[ModelPreset]:
    presets: dict[str, ModelPreset] = request.app.state.model_presets
    return list(presets.values())


@router.get("/presets/gpus", response_model=list[GpuPreset])
def list_gpu_presets(request: Request) -> list[GpuPreset]:
    presets: dict[str, GpuPreset] = request.app.state.gpu_presets
    return list(presets.values())
