"""Tests for per-GPU tensor-parallel sharding + validation (Story 1.5).

Under TP: weights and KV shard across GPUs, but KV's effective divisor is
min(TP, kv_heads) — once TP passes the model's KV-head count, vLLM replicates KV
heads and per-GPU KV stops shrinking (the "replication wall"). Overhead is paid
per GPU (handled in Story 1.4 / assembly). Invalid parallelism raises a typed
error; the replication wall is a warning, not an error (when replication divides
evenly).
"""

import pytest

from vllm_calc_engine.exceptions import InvalidParallelism
from vllm_calc_engine.parallelism import (
    ParallelismPlan,
    plan_tensor_parallel,
    shard_bytes,
)

# Llama-3-70B: 64 attention heads, 8 KV heads.
LLAMA = dict(attention_heads=64, kv_heads=8)


def test_valid_gqa_sharding_no_warning() -> None:
    plan = plan_tensor_parallel(tp=2, gpu_count=2, **LLAMA)
    assert isinstance(plan, ParallelismPlan)
    assert plan.weights_divisor == 2
    assert plan.kv_divisor == 2
    assert plan.warnings == ()


def test_tp_equals_kv_heads_shards_fully() -> None:
    plan = plan_tensor_parallel(tp=8, gpu_count=8, **LLAMA)
    assert plan.kv_divisor == 8
    assert plan.warnings == ()


def test_replication_wall_warns_and_caps_kv_divisor() -> None:
    # TP=16 > 8 KV heads, and 16 % 8 == 0 (even replication) → warning, not error.
    plan = plan_tensor_parallel(tp=16, gpu_count=16, **LLAMA)
    assert plan.weights_divisor == 16  # weights still shard by full TP
    assert plan.kv_divisor == 8  # KV capped at min(TP, kv_heads)
    assert len(plan.warnings) == 1
    assert "kv" in plan.warnings[0].lower() and "16" in plan.warnings[0]


def test_error_when_tp_not_equal_gpu_count() -> None:
    with pytest.raises(InvalidParallelism, match="GPU count"):
        plan_tensor_parallel(tp=2, gpu_count=4, **LLAMA)


def test_error_when_tp_does_not_divide_attention_heads() -> None:
    # TP=3 does not divide 64 attention heads.
    with pytest.raises(InvalidParallelism, match="attention"):
        plan_tensor_parallel(tp=3, gpu_count=3, **LLAMA)


def test_error_when_tp_does_not_divide_kv_heads_below_wall() -> None:
    # TP=4 divides attention (64) but not this model's 6 KV heads (6 % 4 != 0).
    with pytest.raises(InvalidParallelism, match="KV head"):
        plan_tensor_parallel(tp=4, gpu_count=4, attention_heads=64, kv_heads=6)


def test_error_on_uneven_replication_above_wall() -> None:
    # attention 12 % 6 == 0, but TP=6 > kv_heads=4 and 6 % 4 != 0 → uneven replication.
    with pytest.raises(InvalidParallelism, match="replicat"):
        plan_tensor_parallel(tp=6, gpu_count=6, attention_heads=12, kv_heads=4)


def test_tp_one_is_valid_no_sharding() -> None:
    plan = plan_tensor_parallel(tp=1, gpu_count=1, **LLAMA)
    assert plan.weights_divisor == 1
    assert plan.kv_divisor == 1
    assert plan.warnings == ()


def test_shard_bytes_divides() -> None:
    assert shard_bytes(140_000_000_000, 2) == 70_000_000_000
    assert shard_bytes(1_342_177_280, 8) == 167_772_160
    assert isinstance(shard_bytes(100, 3), int)


def test_error_on_nonpositive_tp() -> None:
    with pytest.raises(InvalidParallelism):
        plan_tensor_parallel(tp=0, gpu_count=0, **LLAMA)
