"""Tests for the YAML preset loader (Story 1.7)."""

from pathlib import Path

import pytest

from vllm_calc_api.presets_loader import (
    PresetError,
    load_gpu_presets,
    load_model_presets,
)
from vllm_calc_engine.calculate import calculate
from vllm_calc_engine.models import CalcInput
from vllm_calc_engine.quantization import KVCacheDtype, WeightQuant

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = REPO_ROOT / "presets" / "models"
GPUS_DIR = REPO_ROOT / "presets" / "gpus"


def test_loads_curated_model_presets() -> None:
    models = load_model_presets(MODELS_DIR)
    assert len(models) >= 8
    assert "llama-3.3-70b" in models
    llama = models["llama-3.3-70b"]
    assert llama.kv_heads == 8 and llama.layers == 80 and llama.hidden_size == 8192


def test_loads_curated_gpu_presets() -> None:
    gpus = load_gpu_presets(GPUS_DIR)
    assert len(gpus) >= 6
    assert gpus["a100-80gb"].vram_gib == 80
    assert "mixtral-8x7b" not in gpus  # not a GPU


def test_moe_flag_present() -> None:
    assert load_model_presets(MODELS_DIR)["mixtral-8x7b"].is_moe is True


def test_all_presets_carry_provenance() -> None:
    for p in {**load_model_presets(MODELS_DIR), **load_gpu_presets(GPUS_DIR)}.values():
        assert p.source and p.last_verified


def test_curated_presets_are_engine_ready() -> None:
    # A preset's fields must feed CalcInput and produce a result (id==stem enforced on load).
    m = load_model_presets(MODELS_DIR)["llama-3.3-70b"]
    g = load_gpu_presets(GPUS_DIR)["a100-80gb"]
    result = calculate(
        CalcInput(
            total_params=m.total_params, layers=m.layers, attention_heads=m.attention_heads,
            kv_heads=m.kv_heads, head_dim=m.head_dim, hidden_size=m.hidden_size,
            weight_quant=WeightQuant.AWQ_4BIT, kv_dtype=KVCacheDtype.FP16,
            ctx_len=8192, max_seqs=16, tensor_parallel_size=2, gpu_count=2,
            gpu_vram_gib=g.vram_gib,
        )
    )
    assert result.fits is True


def test_malformed_preset_fails_fast(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("id: broken\nname: Broken\nlayers: -5\n")
    with pytest.raises(PresetError):
        load_model_presets(tmp_path)


def test_id_filename_mismatch_fails(tmp_path: Path) -> None:
    (tmp_path / "a100-80gb.yaml").write_text(
        'id: wrong-id\nname: X\nvram_gib: 80\nsource: s\n'
        'last_verified: "2026-07-09"\nvllm_version_checked: "0.13"\n'
    )
    with pytest.raises(PresetError, match="must match filename stem"):
        load_gpu_presets(tmp_path)
