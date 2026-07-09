"""Provisional calibration constants for the overhead model — ONE PLACE.

⚠️ CALIBRATION TARGETS, NOT MEASURED VALUES. These are engineering estimates
(architecture ranges: fixed context ~1–2 GB/GPU, NCCL ~0.5 GB/GPU, activation
multiplier a small single digit, CUDA graphs ~0.5–2 GB). The Epic 4 validation
harness will tune them against real `vllm serve` startup reserve. They live here,
in one module, so recalibration is a single-file change (Story 1.4 AC).

Bias note: for the conservative-accuracy invariant, prefer values at/above the
measured mean so a "fits" verdict does not OOM.
"""

_GIB = 1024**3
_MIB = 1024**2

# The vLLM version range these estimates are calibrated for (NFR16). Surfaced in
# results and by the API /version endpoint; tightened by the Epic 4 harness.
SUPPORTED_VLLM_RANGE = ">=0.13,<0.14"

# Fixed CUDA context, kernels, cuBLAS/cuDNN workspaces — per GPU, model-independent.
FIXED_CONTEXT_BYTES_PER_GPU = 1 * _GIB

# NCCL communication buffers — added per GPU only when serving on >1 GPU (TP>1).
NCCL_BYTES_PER_GPU = 512 * _MIB

# Activation multiplier "k": residual stream + MLP intermediate + attention buffers.
# activations = max_num_batched_tokens × hidden_size × dtype_bytes × k.
ACTIVATION_MULTIPLIER = 8

# Captured decode CUDA graphs — per GPU; zero when enforce_eager is set.
CUDA_GRAPH_BYTES_PER_GPU = 1 * _GIB
