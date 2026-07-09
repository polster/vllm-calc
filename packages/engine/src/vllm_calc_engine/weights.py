"""Model-weight memory: the fixed VRAM floor.

weights_bytes = total_params × bytes_per_param, returned as integer bytes
(units invariant — the engine computes in bytes, converting to GiB only at
presentation edges).

MoE note: `total_params` must be the model's TOTAL parameter count — every
expert is resident in VRAM even though only some activate per token. Sizing on
the marketed "active" count would badly under-count (e.g. DeepSeek-V3: 37B
active but 671B total).
"""

from vllm_calc_engine.quantization import WeightQuant, weight_bytes_per_param

__all__ = ["weights_bytes"]


def weights_bytes(total_params: int, quant: WeightQuant) -> int:
    """Return weight memory in integer bytes for `total_params` at `quant`.

    Raises:
        ValueError: if `total_params` is negative.
    """
    if total_params < 0:
        raise ValueError(f"total_params must be non-negative, got {total_params}")
    return round(total_params * weight_bytes_per_param(quant))
