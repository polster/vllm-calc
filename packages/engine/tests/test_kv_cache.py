"""Golden-value tests for KV-cache memory (Story 1.3).

KV cache = 2 (K and V) × kv_heads × head_dim × kv_dtype_bytes × layers × ctx_len
× max_seqs, in integer bytes. GQA is captured by using the model's actual
kv_heads; MHA (kv_heads = attention_heads) and MQA (kv_heads = 1) fall out of
the same formula. Quantizing the KV cache (FP8) halves the dtype bytes.
"""

import pytest

from vllm_calc_engine.kv_cache import kv_bytes_per_token, kv_cache_bytes
from vllm_calc_engine.quantization import KVCacheDtype, kv_dtype_bytes

# Llama-3-70B attention shape.
LLAMA70B = dict(layers=80, kv_heads=8, head_dim=128)


def test_kv_dtype_bytes() -> None:
    assert kv_dtype_bytes(KVCacheDtype.FP16) == 2
    assert kv_dtype_bytes(KVCacheDtype.BF16) == 2
    assert kv_dtype_bytes(KVCacheDtype.FP8) == 1


def test_per_token_golden_llama70b_fp16() -> None:
    # 2 * 8 * 128 * 2 * 80 = 327,680 bytes per token (all layers).
    result = kv_bytes_per_token(kv_dtype=KVCacheDtype.FP16, **LLAMA70B)
    assert result == 327_680
    assert isinstance(result, int)


def test_per_token_fp8_halves_fp16() -> None:
    fp16 = kv_bytes_per_token(kv_dtype=KVCacheDtype.FP16, **LLAMA70B)
    fp8 = kv_bytes_per_token(kv_dtype=KVCacheDtype.FP8, **LLAMA70B)
    assert fp8 * 2 == fp16


def test_total_golden_llama70b() -> None:
    # 327,680 * 4096 tokens * 1 seq
    result = kv_cache_bytes(
        kv_dtype=KVCacheDtype.FP16, ctx_len=4096, max_seqs=1, **LLAMA70B
    )
    assert result == 1_342_177_280


def test_total_scales_with_ctx_and_seqs() -> None:
    base = kv_cache_bytes(kv_dtype=KVCacheDtype.FP16, ctx_len=4096, max_seqs=1, **LLAMA70B)
    scaled = kv_cache_bytes(kv_dtype=KVCacheDtype.FP16, ctx_len=8192, max_seqs=4, **LLAMA70B)
    assert scaled == base * 8


@pytest.mark.parametrize(
    ("kv_heads", "label"),
    [(64, "MHA"), (8, "GQA"), (1, "MQA")],
)
def test_same_formula_covers_mha_gqa_mqa(kv_heads: int, label: str) -> None:
    # All three attention styles use the identical formula, parameterized only
    # by kv_heads. MHA (=attention_heads) is largest, MQA (=1) is smallest.
    per_token = kv_bytes_per_token(
        layers=80, kv_heads=kv_heads, head_dim=128, kv_dtype=KVCacheDtype.FP16
    )
    assert per_token == 2 * kv_heads * 128 * 2 * 80


def test_reject_nonpositive_inputs() -> None:
    with pytest.raises(ValueError):
        kv_bytes_per_token(layers=0, kv_heads=8, head_dim=128, kv_dtype=KVCacheDtype.FP16)
    with pytest.raises(ValueError):
        kv_cache_bytes(
            layers=80, kv_heads=8, head_dim=128,
            kv_dtype=KVCacheDtype.FP16, ctx_len=-1, max_seqs=1,
        )
