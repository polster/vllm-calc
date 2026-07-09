"""Per-GPU tensor-parallel sharding and validation.

Weights shard by the full TP; the KV cache shards only by `min(TP, kv_heads)` —
once TP exceeds the model's KV-head count, vLLM replicates KV heads and per-GPU
KV stops shrinking (the "replication wall", a warning, not an error, when
replication divides evenly). Validation mirrors vLLM's real constraints:

    * TP must equal the GPU count.
    * attention_heads must be divisible by TP.
    * KV heads: if TP <= kv_heads, kv_heads must be divisible by TP (normal GQA
      sharding); if TP > kv_heads, TP must be divisible by kv_heads (even
      replication) — and we warn.
"""

from dataclasses import dataclass

from vllm_calc_engine.exceptions import InvalidParallelism

__all__ = ["ParallelismPlan", "plan_tensor_parallel", "shard_bytes"]


@dataclass(frozen=True)
class ParallelismPlan:
    """How weights and KV divide across GPUs under a validated TP config."""

    tp: int
    weights_divisor: int  # == tp
    kv_divisor: int  # == min(tp, kv_heads)
    warnings: tuple[str, ...]


def plan_tensor_parallel(
    *, tp: int, gpu_count: int, attention_heads: int, kv_heads: int
) -> ParallelismPlan:
    """Validate a TP config and return the per-GPU sharding plan.

    Raises:
        InvalidParallelism: on non-positive TP, TP != gpu_count, attention-head
            indivisibility, KV-head indivisibility below the wall, or uneven
            replication above the wall.
    """
    if tp <= 0:
        raise InvalidParallelism(f"tensor-parallel size must be positive, got {tp}")
    if tp != gpu_count:
        raise InvalidParallelism(
            f"tensor-parallel size ({tp}) must equal the GPU count ({gpu_count})"
        )
    if attention_heads % tp != 0:
        raise InvalidParallelism(
            f"tensor-parallel size ({tp}) must divide the number of attention heads "
            f"({attention_heads})"
        )

    warnings: list[str] = []
    if tp <= kv_heads:
        if kv_heads % tp != 0:
            raise InvalidParallelism(
                f"tensor-parallel size ({tp}) must divide the number of KV heads ({kv_heads})"
            )
        kv_divisor = tp
    else:
        # Replication wall: TP exceeds KV heads → each GPU holds >=1 replicated KV head.
        if tp % kv_heads != 0:
            raise InvalidParallelism(
                f"tensor-parallel size ({tp}) exceeds KV heads ({kv_heads}) but does not "
                f"replicate evenly ({tp} % {kv_heads} != 0)"
            )
        kv_divisor = kv_heads
        warnings.append(
            f"KV-replication wall: TP ({tp}) exceeds this model's {kv_heads} KV heads; "
            f"the KV cache will not shard further (each GPU holds >=1 replicated KV head). "
            f"Extra GPUs beyond {kv_heads} add overhead without reducing per-GPU KV — "
            f"consider fewer GPUs or (future) pipeline parallelism."
        )

    return ParallelismPlan(
        tp=tp, weights_divisor=tp, kv_divisor=kv_divisor, warnings=tuple(warnings)
    )


def shard_bytes(total_bytes: int, divisor: int) -> int:
    """Divide a total byte count across `divisor` GPUs, returned as integer bytes."""
    if divisor <= 0:
        raise InvalidParallelism(f"divisor must be positive, got {divisor}")
    return round(total_bytes / divisor)
