"""Golden-value tests for model-weight memory (Story 1.2).

Weights are the fixed VRAM floor: total_params × bytes_per_param, in integer
bytes (units invariant). Quantization sets bytes_per_param. MoE models must use
TOTAL parameters (all experts resident), never the marketed "active" count.
"""

import pytest

from vllm_calc_engine.quantization import WeightQuant, weight_bytes_per_param
from vllm_calc_engine.weights import weights_bytes


@pytest.mark.parametrize(
    ("quant", "expected_bpp"),
    [
        (WeightQuant.FP32, 4.0),
        (WeightQuant.FP16, 2.0),
        (WeightQuant.BF16, 2.0),
        (WeightQuant.FP8, 1.0),
        (WeightQuant.INT8, 1.0),
        (WeightQuant.AWQ_4BIT, 0.5),
        (WeightQuant.GPTQ_4BIT, 0.5),
    ],
)
def test_weight_bytes_per_param(quant: WeightQuant, expected_bpp: float) -> None:
    assert weight_bytes_per_param(quant) == expected_bpp


@pytest.mark.parametrize(
    ("quant", "expected_bytes"),
    [
        # 70B params, golden values in integer bytes.
        (WeightQuant.FP16, 140_000_000_000),
        (WeightQuant.FP8, 70_000_000_000),
        (WeightQuant.AWQ_4BIT, 35_000_000_000),
        (WeightQuant.GPTQ_4BIT, 35_000_000_000),
    ],
)
def test_weights_bytes_golden_70b(quant: WeightQuant, expected_bytes: int) -> None:
    result = weights_bytes(70_000_000_000, quant)
    assert result == expected_bytes
    assert isinstance(result, int)  # units invariant: integer bytes, never float


def test_moe_uses_total_not_active_params() -> None:
    # Mixtral-8x7B-style: ~46.7B TOTAL params resident, ~12.9B "active".
    # The engine must size on TOTAL — sizing on active would badly under-count.
    total_params = 46_700_000_000
    active_params = 12_900_000_000
    total_fp16 = weights_bytes(total_params, WeightQuant.FP16)
    active_fp16 = weights_bytes(active_params, WeightQuant.FP16)
    assert total_fp16 == 93_400_000_000
    assert total_fp16 > active_fp16  # sizing on total, not active


def test_weights_reject_negative_params() -> None:
    with pytest.raises(ValueError):
        weights_bytes(-1, WeightQuant.FP16)
