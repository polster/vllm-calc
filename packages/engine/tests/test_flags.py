"""Tests for honesty flags on the result (Story 2.4).

Known-conservative architectures (MLA, sliding-window) and uncalibrated ones must
be *flagged in the result*, never thrown — the user always gets a labeled number
instead of a silently-wrong one (NFR4 / FR21).
"""

from vllm_calc_engine.attention import AttentionType
from vllm_calc_engine.calculate import calculate
from vllm_calc_engine.flags import build_flags
from vllm_calc_engine.models import CalcInput
from vllm_calc_engine.quantization import KVCacheDtype, WeightQuant

BASE = CalcInput(
    total_params=70_000_000_000,
    layers=80,
    attention_heads=64,
    kv_heads=8,
    head_dim=128,
    hidden_size=8192,
    weight_quant=WeightQuant.AWQ_4BIT,
    kv_dtype=KVCacheDtype.FP16,
    ctx_len=8192,
    max_seqs=32,
    tensor_parallel_size=2,
    gpu_count=2,
    gpu_vram_gib=80,
    gpu_memory_utilization=0.9,
)


def test_standard_attention_has_no_flags() -> None:
    assert build_flags(BASE) == []
    assert calculate(BASE).flags == []


def test_mla_is_flagged_as_over_provision() -> None:
    flags = build_flags(BASE.model_copy(update={"attention_type": AttentionType.MLA}))
    assert len(flags) == 1
    assert flags[0].type == "over_provision_estimate"
    assert "MLA" in flags[0].message


def test_sliding_window_is_flagged_as_over_provision() -> None:
    flags = build_flags(
        BASE.model_copy(update={"attention_type": AttentionType.SLIDING_WINDOW})
    )
    assert flags[0].type == "over_provision_estimate"
    assert "sliding" in flags[0].message.lower()


def test_other_architecture_is_flagged_unsupported() -> None:
    flags = build_flags(BASE.model_copy(update={"attention_type": AttentionType.OTHER}))
    assert flags[0].type == "unsupported"


def test_flags_are_carried_not_thrown_and_calculation_still_runs() -> None:
    # An uncalibrated architecture still returns a full, labeled result.
    r = calculate(BASE.model_copy(update={"attention_type": AttentionType.OTHER}))
    assert r.fits in (True, False)  # a real verdict was produced
    assert any(f.type == "unsupported" for f in r.flags)
