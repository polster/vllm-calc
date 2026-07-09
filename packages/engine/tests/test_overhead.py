"""Tests for the three-term overhead model (Story 1.4).

overhead_per_gpu = fixed_context (+NCCL when multi-GPU) + activations + cuda_graphs.
Replaces the industry-standard flat "weights × %" fudge. Constants are PROVISIONAL
calibration targets (Epic 4 harness); these tests pin the *structure and behavior*,
not the eventual calibrated magnitudes.
"""

import pytest

from vllm_calc_engine import constants
from vllm_calc_engine.overhead import OverheadBreakdown, overhead_bytes

GIB = 1024**3
DEFAULTS = dict(hidden_size=8192, max_num_batched_tokens=2048, dtype_bytes=2)


def test_activation_term_formula() -> None:
    # activations = max_num_batched_tokens × hidden_size × dtype_bytes × k
    ob = overhead_bytes(gpu_count=1, enforce_eager=False, **DEFAULTS)
    expected = 2048 * 8192 * 2 * constants.ACTIVATION_MULTIPLIER
    assert ob.activations == expected
    assert isinstance(ob.activations, int)


def test_single_gpu_no_nccl_and_total_is_sum() -> None:
    ob = overhead_bytes(gpu_count=1, enforce_eager=False, **DEFAULTS)
    assert ob.fixed_context == constants.FIXED_CONTEXT_BYTES_PER_GPU  # no NCCL on 1 GPU
    assert ob.cuda_graphs == constants.CUDA_GRAPH_BYTES_PER_GPU
    assert ob.total == ob.fixed_context + ob.activations + ob.cuda_graphs


def test_multi_gpu_adds_nccl_to_fixed_context() -> None:
    one = overhead_bytes(gpu_count=1, enforce_eager=False, **DEFAULTS)
    two = overhead_bytes(gpu_count=2, enforce_eager=False, **DEFAULTS)
    assert two.fixed_context == one.fixed_context + constants.NCCL_BYTES_PER_GPU


def test_enforce_eager_zeroes_cuda_graphs() -> None:
    eager = overhead_bytes(gpu_count=1, enforce_eager=True, **DEFAULTS)
    graphs = overhead_bytes(gpu_count=1, enforce_eager=False, **DEFAULTS)
    assert eager.cuda_graphs == 0
    assert graphs.cuda_graphs == constants.CUDA_GRAPH_BYTES_PER_GPU
    assert eager.total == graphs.total - constants.CUDA_GRAPH_BYTES_PER_GPU


def test_activations_scale_with_token_budget_and_hidden() -> None:
    base = overhead_bytes(gpu_count=1, enforce_eager=True, hidden_size=8192,
                          max_num_batched_tokens=2048, dtype_bytes=2)
    bigger = overhead_bytes(gpu_count=1, enforce_eager=True, hidden_size=16384,
                            max_num_batched_tokens=4096, dtype_bytes=2)
    assert bigger.activations == base.activations * 4


def test_returns_breakdown_with_three_subterms() -> None:
    ob = overhead_bytes(gpu_count=1, enforce_eager=False, **DEFAULTS)
    assert isinstance(ob, OverheadBreakdown)
    # "show your work": the three sub-terms are individually available.
    assert {"fixed_context", "activations", "cuda_graphs", "total"} <= set(vars(ob))


def test_calibration_constants_live_in_one_place() -> None:
    # AC: constants defined in one module (calibration targets for Epic 4).
    for name in (
        "FIXED_CONTEXT_BYTES_PER_GPU",
        "NCCL_BYTES_PER_GPU",
        "ACTIVATION_MULTIPLIER",
        "CUDA_GRAPH_BYTES_PER_GPU",
    ):
        assert getattr(constants, name) > 0


def test_reject_nonpositive_inputs() -> None:
    with pytest.raises(ValueError):
        overhead_bytes(gpu_count=0, enforce_eager=False, **DEFAULTS)
    with pytest.raises(ValueError):
        overhead_bytes(gpu_count=1, enforce_eager=False, hidden_size=0,
                       max_num_batched_tokens=2048, dtype_bytes=2)
