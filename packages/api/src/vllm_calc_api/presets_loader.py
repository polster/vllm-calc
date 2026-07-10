"""Load and validate version-controlled YAML presets into memory.

Presets are data, not code (adding one needs no code change). Each YAML file is
validated against the engine-owned Pydantic schema; a schema violation or an
id/filename mismatch fails fast (raises) so a bad preset can never reach users.
"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from vllm_calc_engine.models import GpuPreset, ModelPreset

__all__ = ["PresetError", "load_model_presets", "load_gpu_presets"]


class PresetError(Exception):
    """A preset file is malformed, invalid, or misnamed."""


def _load_dir[T: (ModelPreset, GpuPreset)](directory: Path, model: type[T]) -> dict[str, T]:
    presets: dict[str, T] = {}
    for path in sorted(directory.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text())
        if not isinstance(raw, dict):
            raise PresetError(f"{path}: expected a YAML mapping, got {type(raw).__name__}")
        try:
            preset = model.model_validate(raw)
        except ValidationError as exc:
            raise PresetError(f"{path}: does not match {model.__name__} schema:\n{exc}") from exc
        if preset.id != path.stem:
            raise PresetError(f"{path}: id '{preset.id}' must match filename stem '{path.stem}'")
        if preset.id in presets:
            raise PresetError(f"duplicate preset id '{preset.id}'")
        presets[preset.id] = preset
    return presets


def load_model_presets(directory: Path) -> dict[str, ModelPreset]:
    """Load all model presets from `directory/*.yaml`, keyed by id."""
    return _load_dir(directory, ModelPreset)


def load_gpu_presets(directory: Path) -> dict[str, GpuPreset]:
    """Load all GPU presets from `directory/*.yaml`, keyed by id."""
    return _load_dir(directory, GpuPreset)
