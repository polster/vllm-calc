"""Top-level orchestration: compose the four consumers into the fit verdict.

This is the engine's single entry point. It shards weights and KV per GPU,
adds per-GPU overhead, and derives serving capacity:

    available_for_kv = gpu_util × vram_per_gpu − weights_per_gpu − overhead_per_gpu
    max_concurrent   = min(max_num_seqs_cap, ⌊available_for_kv / kv_bytes_per_seq⌋)
    fits            ⟺ max_seqs ≤ max_concurrent

All math is in integer bytes; the only unit conversion is GiB→bytes at the input
edge. Deterministic and pure (NFR3).
"""

from vllm_calc_engine import constants
from vllm_calc_engine.command import serve_command
from vllm_calc_engine.kv_cache import kv_bytes_per_token
from vllm_calc_engine.models import Breakdown, CalcInput, CalcResult
from vllm_calc_engine.overhead import overhead_bytes
from vllm_calc_engine.parallelism import plan_tensor_parallel, shard_bytes
from vllm_calc_engine.remediation import build_remediations
from vllm_calc_engine.weights import weights_bytes

__all__ = ["calculate"]

_GIB = 1024**3
# Activations are computed in the model's compute dtype (fp16/bf16), independent
# of weight quantization (quantized weights dequantize for matmul).
_ACTIVATION_DTYPE_BYTES = 2


def calculate(inp: CalcInput) -> CalcResult:
    """Compute the full sizing result, adding remediations on a no-go.

    Raises InvalidParallelism on a bad TP config.
    """
    result = _compute(inp)
    if not result.fits:
        result.remediations = build_remediations(inp, result, _compute)
    return result


def _compute(inp: CalcInput) -> CalcResult:
    """The core sizing computation (no remediations); reused to evaluate fixes."""
    plan = plan_tensor_parallel(
        tp=inp.tensor_parallel_size,
        gpu_count=inp.gpu_count,
        attention_heads=inp.attention_heads,
        kv_heads=inp.kv_heads,
    )

    # Weights (sharded by full TP).
    weights_pg = shard_bytes(
        weights_bytes(inp.total_params, inp.weight_quant), plan.weights_divisor
    )

    # KV: per-token bytes sharded by min(TP, kv_heads); then a per-sequence cost.
    per_token_total = kv_bytes_per_token(
        layers=inp.layers, kv_heads=inp.kv_heads, head_dim=inp.head_dim, kv_dtype=inp.kv_dtype
    )
    per_token_pg = shard_bytes(per_token_total, plan.kv_divisor)
    kv_bytes_per_seq = per_token_pg * inp.ctx_len
    kv_pg_requested = kv_bytes_per_seq * inp.max_seqs

    # Overhead (per GPU).
    oh = overhead_bytes(
        gpu_count=inp.gpu_count,
        hidden_size=inp.hidden_size,
        max_num_batched_tokens=inp.max_num_batched_tokens,
        dtype_bytes=_ACTIVATION_DTYPE_BYTES,
        enforce_eager=inp.enforce_eager,
    )

    # Budget and capacity.
    budget_pg = round(inp.gpu_vram_gib * _GIB * inp.gpu_memory_utilization)
    available_for_kv = budget_pg - weights_pg - oh.total
    kv_limited = available_for_kv // kv_bytes_per_seq if available_for_kv > 0 else 0
    max_concurrent = max(0, min(inp.max_num_seqs_cap, kv_limited))
    fits = inp.max_seqs <= max_concurrent

    used_pg = weights_pg + oh.total + kv_pg_requested

    if available_for_kv <= 0:
        verdict = (
            f"Won't fit — weights + overhead alone ({(weights_pg + oh.total) / _GIB:.1f} GiB) "
            f"exceed the per-GPU budget ({budget_pg / _GIB:.1f} GiB)."
        )
    elif fits:
        verdict = (
            f"Fits — supports up to {max_concurrent} concurrent sequences "
            f"(you asked for {inp.max_seqs})."
        )
    else:
        verdict = (
            f"Won't fit — supports up to {max_concurrent} concurrent sequences, "
            f"but you asked for {inp.max_seqs}. Reduce concurrency or context, or add a GPU."
        )

    return CalcResult(
        fits=fits,
        requested_max_seqs=inp.max_seqs,
        max_concurrent=max_concurrent,
        verdict=verdict,
        worst_case_note=(
            "Conservative: max_concurrent assumes every sequence uses the full context "
            "length. With PagedAttention, real capacity is usually higher."
        ),
        supported_vllm_range=constants.SUPPORTED_VLLM_RANGE,
        warnings=list(plan.warnings),
        serve_command=serve_command(inp),
        breakdown=Breakdown(
            weights_per_gpu_bytes=weights_pg,
            kv_per_gpu_bytes=kv_pg_requested,
            overhead_fixed_context_bytes=oh.fixed_context,
            overhead_activations_bytes=oh.activations,
            overhead_cuda_graphs_bytes=oh.cuda_graphs,
            overhead_total_bytes=oh.total,
            used_per_gpu_bytes=used_pg,
            budget_per_gpu_bytes=budget_pg,
            available_for_kv_bytes=available_for_kv,
        ),
    )
