"""Attention variants that affect how honestly we can size the KV cache.

The v1 engine uses one generic KV formula. For MLA and sliding-window attention
that formula *over-provisions* (a conservative over-estimate); for architectures
we haven't calibrated at all it may be wrong in either direction. Rather than
branch the math (deferred), we carry a flag so the number is never silently wrong.
"""

from enum import StrEnum

__all__ = ["AttentionType"]


class AttentionType(StrEnum):
    STANDARD = "standard"  # MHA / GQA / MQA — the generic formula is accurate
    MLA = "mla"  # multi-head latent attention — generic formula over-provisions
    SLIDING_WINDOW = "sliding_window"  # generic formula over-provisions
    OTHER = "other"  # not specifically calibrated — flag as unsupported
