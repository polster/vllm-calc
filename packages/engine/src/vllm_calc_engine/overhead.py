"""The three-term overhead model (per GPU).

Replaces the industry-standard flat "weights × %" fudge with mechanisms that
actually scale the way vLLM's reserve does:

    overhead = fixed_context (+NCCL when multi-GPU)   # scales with nothing
             + activations                            # scales with tokens-in-flight × hidden
             + cuda_graphs                            # semi-fixed; zero under enforce_eager

All integer bytes. The three sub-terms are returned individually so the UI can
"show its work" (expandable overhead). Magnitudes come from provisional
calibration constants (see `constants.py`).
"""

from dataclasses import dataclass

from vllm_calc_engine import constants

__all__ = ["OverheadBreakdown", "overhead_bytes"]


@dataclass(frozen=True)
class OverheadBreakdown:
    """Per-GPU overhead, itemized for the 'show your work' UI."""

    fixed_context: int  # CUDA context + kernels + workspaces (+NCCL if multi-GPU)
    activations: int  # transient forward-pass scratch, bounded by the token budget
    cuda_graphs: int  # captured decode graphs (0 under enforce_eager)
    total: int


def overhead_bytes(
    *,
    gpu_count: int,
    hidden_size: int,
    max_num_batched_tokens: int,
    dtype_bytes: int,
    enforce_eager: bool,
) -> OverheadBreakdown:
    """Compute per-GPU overhead as a three-term breakdown.

    Raises:
        ValueError: if any numeric input is not positive.
    """
    if gpu_count <= 0 or hidden_size <= 0 or max_num_batched_tokens <= 0 or dtype_bytes <= 0:
        raise ValueError(
            "gpu_count, hidden_size, max_num_batched_tokens, dtype_bytes must be positive; "
            f"got gpu_count={gpu_count}, hidden_size={hidden_size}, "
            f"max_num_batched_tokens={max_num_batched_tokens}, dtype_bytes={dtype_bytes}"
        )

    fixed_context = constants.FIXED_CONTEXT_BYTES_PER_GPU
    if gpu_count > 1:
        fixed_context += constants.NCCL_BYTES_PER_GPU

    activations = (
        max_num_batched_tokens * hidden_size * dtype_bytes * constants.ACTIVATION_MULTIPLIER
    )

    cuda_graphs = 0 if enforce_eager else constants.CUDA_GRAPH_BYTES_PER_GPU

    return OverheadBreakdown(
        fixed_context=fixed_context,
        activations=activations,
        cuda_graphs=cuda_graphs,
        total=fixed_context + activations + cuda_graphs,
    )
