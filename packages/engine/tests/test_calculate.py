"""End-to-end golden test for the assembled verdict + capacity (Story 1.6).

Composes weights + KV + 3-term overhead + per-GPU TP sharding into the headline
result: available_for_kv → max_concurrent → fits ⟺ max_seqs ≤ max_concurrent.
The golden scenario locks the exact assembled byte values so any drift in the
engine is caught.
"""

import pytest

from vllm_calc_engine.calculate import calculate
from vllm_calc_engine.exceptions import InvalidParallelism
from vllm_calc_engine.models import CalcInput
from vllm_calc_engine.quantization import KVCacheDtype, WeightQuant

GIB = 1024**3

# Llama-3.3-70B, AWQ 4-bit, on 2× A100 80GB, TP=2, 8k context, 32 concurrent.
LLAMA_70B_2xA100 = CalcInput(
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


def test_golden_llama70b_2xa100_fits() -> None:
    r = calculate(LLAMA_70B_2xA100)
    b = r.breakdown
    assert b.weights_per_gpu_bytes == 17_500_000_000  # 70B × 0.5 / TP2
    assert b.overhead_total_bytes == 2_952_790_016  # fixed+NCCL + activations + graphs
    assert b.budget_per_gpu_bytes == round(80 * GIB * 0.9)  # 77,309,411,328
    assert b.available_for_kv_bytes == 56_856_621_312
    assert r.max_concurrent == 42  # KV-limited; below the 256 batch cap
    assert r.requested_max_seqs == 32
    assert r.fits is True
    assert "42" in r.verdict and "32" in r.verdict
    assert r.worst_case_note  # non-empty conservative label
    assert r.supported_vllm_range.startswith(">=0.13")
    assert r.warnings == []  # TP=2 ≤ 8 kv_heads: no replication wall


def test_no_go_when_context_too_large() -> None:
    r = calculate(LLAMA_70B_2xA100.model_copy(update={"ctx_len": 131072, "max_seqs": 32}))
    assert r.fits is False
    assert r.max_concurrent < 32
    assert "fit" in r.verdict.lower()


def test_batch_cap_bounds_max_concurrent() -> None:
    # Tiny model, huge budget → capacity is capped by max_num_seqs_cap, not KV.
    r = calculate(
        LLAMA_70B_2xA100.model_copy(
            update={"total_params": 1_000_000_000, "ctx_len": 512, "max_num_seqs_cap": 64}
        )
    )
    assert r.max_concurrent == 64


def test_replication_wall_warning_propagates() -> None:
    r = calculate(
        LLAMA_70B_2xA100.model_copy(update={"tensor_parallel_size": 16, "gpu_count": 16})
    )
    assert any("replication" in w.lower() for w in r.warnings)


def test_invalid_parallelism_raises() -> None:
    with pytest.raises(InvalidParallelism):
        calculate(LLAMA_70B_2xA100.model_copy(update={"tensor_parallel_size": 3, "gpu_count": 3}))


def test_result_is_deterministic() -> None:
    assert calculate(LLAMA_70B_2xA100) == calculate(LLAMA_70B_2xA100)
