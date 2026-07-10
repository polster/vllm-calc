"""Validate version-controlled presets in CI (Story 4.1).

Every preset is validated against the engine's Pydantic schema (the loader does
this, fail-fast) and must carry full provenance (source, last_verified,
vllm_version_checked — enforced by the required schema fields). A suspiciously low
param count for a known-MoE model raises a *warning* (a common contributor mistake
is entering ACTIVE instead of TOTAL params); warnings don't fail the build.

Run:  uv run python -m vllm_calc_api.preset_validation
"""

import json
import sys
from pathlib import Path

from vllm_calc_api import settings
from vllm_calc_api.presets_loader import PresetError, load_gpu_presets, load_model_presets
from vllm_calc_engine.models import GpuPreset, ModelPreset

__all__ = ["moe_param_warnings", "validate_presets", "write_schemas", "main"]

# A dense modern MoE is tens of billions of params total (Mixtral-8x7B is 46.7B).
# Below this, a "MoE" preset most likely holds ACTIVE params by mistake.
MOE_MIN_TOTAL_PARAMS = 15_000_000_000


def moe_param_warnings(models: dict[str, ModelPreset]) -> list[str]:
    """Advisory warnings for MoE presets whose total_params looks implausibly low."""
    warnings: list[str] = []
    for m in models.values():
        if m.is_moe and m.total_params < MOE_MIN_TOTAL_PARAMS:
            warnings.append(
                f"{m.id}: is_moe but total_params={m.total_params:,} looks low — "
                f"did you enter ACTIVE instead of TOTAL (all-experts) params?"
            )
    return warnings


def validate_presets(base: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). A non-empty errors list means the build should fail."""
    errors: list[str] = []
    try:
        models = load_model_presets(base / "models")
        load_gpu_presets(base / "gpus")
    except PresetError as exc:
        return [str(exc)], []
    return errors, moe_param_warnings(models)


def write_schemas(schema_dir: Path) -> None:
    """Generate JSON Schema files from the engine's Pydantic preset models."""
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "model.schema.json").write_text(
        json.dumps(ModelPreset.model_json_schema(), indent=2) + "\n"
    )
    (schema_dir / "gpu.schema.json").write_text(
        json.dumps(GpuPreset.model_json_schema(), indent=2) + "\n"
    )


def main() -> int:
    base = settings.presets_dir()
    errors, warnings = validate_presets(base)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        return 1
    models = load_model_presets(base / "models")
    gpus = load_gpu_presets(base / "gpus")
    print(f"OK: {len(models)} model + {len(gpus)} GPU presets valid ({len(warnings)} warnings).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
