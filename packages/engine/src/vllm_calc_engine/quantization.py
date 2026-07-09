"""Quantization schemes and their weight cost in bytes-per-parameter.

Story 1.2 covers weight quantization only. KV-cache dtype is modeled separately
in Story 1.3. Schemes are a str enum so they serialize cleanly in the API/CLI
later. Extending the set (new formats) is additive — no core rewrite (NFR14).
"""

from enum import StrEnum

__all__ = [
    "WeightQuant",
    "weight_bytes_per_param",
    "KVCacheDtype",
    "kv_dtype_bytes",
]


class WeightQuant(StrEnum):
    """A quantization scheme applied to model weights."""

    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    FP8 = "fp8"
    INT8 = "int8"
    AWQ_4BIT = "awq-4bit"
    GPTQ_4BIT = "gptq-4bit"


# Bytes stored per parameter for each scheme. 4-bit formats pack two params per
# byte (0.5). These are the dominant term; packing metadata (scales/zeros) is a
# small correction folded into overhead, not here.
_BYTES_PER_PARAM: dict[WeightQuant, float] = {
    WeightQuant.FP32: 4.0,
    WeightQuant.FP16: 2.0,
    WeightQuant.BF16: 2.0,
    WeightQuant.FP8: 1.0,
    WeightQuant.INT8: 1.0,
    WeightQuant.AWQ_4BIT: 0.5,
    WeightQuant.GPTQ_4BIT: 0.5,
}


def weight_bytes_per_param(quant: WeightQuant) -> float:
    """Return the bytes stored per parameter for a weight quantization scheme."""
    return _BYTES_PER_PARAM[quant]


class KVCacheDtype(StrEnum):
    """The dtype the KV cache is stored in (independent of weight quantization)."""

    FP16 = "fp16"
    BF16 = "bf16"
    FP8 = "fp8"


_KV_DTYPE_BYTES: dict[KVCacheDtype, int] = {
    KVCacheDtype.FP16: 2,
    KVCacheDtype.BF16: 2,
    KVCacheDtype.FP8: 1,
}


def kv_dtype_bytes(dtype: KVCacheDtype) -> int:
    """Return the bytes-per-element the KV cache uses for a given dtype."""
    return _KV_DTYPE_BYTES[dtype]
