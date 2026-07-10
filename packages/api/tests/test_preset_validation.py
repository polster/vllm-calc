"""Tests for preset validation + provenance (Story 4.1)."""

from pathlib import Path

import pytest
import yaml

from vllm_calc_api import settings
from vllm_calc_api.preset_validation import (
    MOE_MIN_TOTAL_PARAMS,
    moe_param_warnings,
    validate_presets,
)
from vllm_calc_api.presets_loader import PresetError, load_model_presets

MIXTRAL = {
    "id": "mixtral-8x7b",
    "name": "Mixtral 8x7B",
    "total_params": 46_700_000_000,
    "layers": 32,
    "attention_heads": 32,
    "kv_heads": 8,
    "head_dim": 128,
    "hidden_size": 4096,
    "is_moe": True,
    "source": "https://huggingface.co/mistralai/Mixtral-8x7B-v0.1",
    "last_verified": "2026-07-09",
    "vllm_version_checked": "0.13",
}


def _write(dir_: Path, stem: str, data: dict[str, object]) -> None:
    (dir_ / f"{stem}.yaml").write_text(yaml.safe_dump(data))


def test_shipped_presets_validate_cleanly() -> None:
    errors, warnings = validate_presets(settings.presets_dir())
    assert errors == []
    assert warnings == []  # curated baseline has no low-param MoE


def test_low_param_moe_raises_a_warning() -> None:
    models = {
        "mixtral-8x7b": load_model_presets(settings.presets_dir() / "models")["mixtral-8x7b"],
    }
    # Sanity: the real Mixtral is above the threshold and does not warn.
    assert moe_param_warnings(models) == []
    # A MoE with active-only params (below the threshold) warns.
    low = models["mixtral-8x7b"].model_copy(update={"total_params": MOE_MIN_TOTAL_PARAMS - 1})
    warnings = moe_param_warnings({"low": low})
    assert len(warnings) == 1 and "ACTIVE" in warnings[0]


def test_missing_provenance_field_fails_validation(tmp_path: Path) -> None:
    (tmp_path / "models").mkdir()
    (tmp_path / "gpus").mkdir()
    incomplete = {k: v for k, v in MIXTRAL.items() if k != "vllm_version_checked"}
    _write(tmp_path / "models", "mixtral-8x7b", incomplete)
    errors, _ = validate_presets(tmp_path)
    assert errors and "vllm_version_checked" in errors[0]


def test_id_filename_mismatch_still_fails(tmp_path: Path) -> None:
    (tmp_path / "models").mkdir()
    _write(tmp_path / "models", "wrong-name", MIXTRAL)
    with pytest.raises(PresetError):
        load_model_presets(tmp_path / "models")
