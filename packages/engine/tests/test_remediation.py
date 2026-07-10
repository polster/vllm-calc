"""Tests for no-go remediation suggestions (Story 2.2).

The load-bearing invariant is honesty: every remediation the engine offers must,
when its delta is applied, actually turn the no-go into a fit. We never suggest a
fix that doesn't work.
"""

from vllm_calc_engine.calculate import calculate
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
# 128k context on the same box: a clear no-go with some (but insufficient) capacity.
NOGO = BASE.model_copy(update={"ctx_len": 131072, "max_seqs": 32})


def test_fitting_config_has_no_remediations() -> None:
    r = calculate(BASE)
    assert r.fits
    assert r.remediations == []


def test_no_go_offers_at_least_one_fix() -> None:
    r = calculate(NOGO)
    assert not r.fits
    assert len(r.remediations) >= 1


def test_every_remediation_actually_fits() -> None:
    r = calculate(NOGO)
    for rem in r.remediations:
        applied = NOGO.model_copy(update=rem.delta)
        assert calculate(applied).fits, f"remediation {rem.label!r} does not actually fit"


def test_reduce_concurrency_targets_the_supported_capacity() -> None:
    r = calculate(NOGO)
    mc = r.max_concurrent
    assert mc >= 1  # this scenario has some capacity, just not enough
    assert any(rem.delta.get("max_seqs") == mc for rem in r.remediations)


def test_higher_tp_suggestions_are_valid_divisors() -> None:
    r = calculate(NOGO)
    for rem in r.remediations:
        tp = rem.delta.get("tensor_parallel_size")
        if tp is not None:
            assert isinstance(tp, int) and NOGO.attention_heads % tp == 0


def test_fp8_kv_offered_only_when_not_already_fp8() -> None:
    # A config already on FP8 KV must not suggest "switch to FP8 KV".
    already_fp8 = NOGO.model_copy(update={"kv_dtype": KVCacheDtype.FP8})
    r = calculate(already_fp8)
    assert all("kv_dtype" not in rem.delta for rem in r.remediations)


def test_remediations_are_capped() -> None:
    assert len(calculate(NOGO).remediations) <= 4
