"""KV-cache memory — the dynamic term that decides serving capacity.

Per token, across all layers:
    2 (K and V) × kv_heads × head_dim × kv_dtype_bytes × layers
Total:
    per_token × ctx_len × max_seqs

All integer bytes (units invariant). GQA is captured by passing the model's
actual `kv_heads`; MHA (kv_heads = attention_heads) and MQA (kv_heads = 1) use
the identical formula. This generic form intentionally over-estimates MLA
(DeepSeek) and sliding-window models — conservative is the safe direction for a
sizing tool; exact per-architecture math is a deferred fast-follow.
"""

from vllm_calc_engine.quantization import KVCacheDtype, kv_dtype_bytes

__all__ = ["kv_bytes_per_token", "kv_cache_bytes"]


def kv_bytes_per_token(
    *, layers: int, kv_heads: int, head_dim: int, kv_dtype: KVCacheDtype
) -> int:
    """Bytes of KV cache one token occupies across all layers.

    Raises:
        ValueError: if layers, kv_heads, or head_dim is not positive.
    """
    if layers <= 0 or kv_heads <= 0 or head_dim <= 0:
        raise ValueError(
            f"layers, kv_heads, head_dim must be positive; "
            f"got layers={layers}, kv_heads={kv_heads}, head_dim={head_dim}"
        )
    return 2 * kv_heads * head_dim * kv_dtype_bytes(kv_dtype) * layers


def kv_cache_bytes(
    *,
    layers: int,
    kv_heads: int,
    head_dim: int,
    kv_dtype: KVCacheDtype,
    ctx_len: int,
    max_seqs: int,
) -> int:
    """Total KV-cache bytes for `max_seqs` sequences each up to `ctx_len` tokens.

    Raises:
        ValueError: if any dimension is not positive.
    """
    if ctx_len <= 0 or max_seqs <= 0:
        raise ValueError(
            f"ctx_len and max_seqs must be positive; got ctx_len={ctx_len}, max_seqs={max_seqs}"
        )
    return (
        kv_bytes_per_token(layers=layers, kv_heads=kv_heads, head_dim=head_dim, kv_dtype=kv_dtype)
        * ctx_len
        * max_seqs
    )
