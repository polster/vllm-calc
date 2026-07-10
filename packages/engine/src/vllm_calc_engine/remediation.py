"""Suggest nearest fitting configurations for a no-go result (Story 2.2).

Each suggestion is a single, explainable lever change carrying the exact input
delta to apply. The honesty rule: a candidate is only offered if applying it
genuinely flips the result to `fits` — verified by re-running the compute. To
avoid an import cycle (calculate → remediation → calculate), the compute entry
point is injected rather than imported.
"""

from collections.abc import Callable

from vllm_calc_engine.exceptions import InvalidParallelism
from vllm_calc_engine.models import CalcInput, CalcResult, Remediation
from vllm_calc_engine.quantization import KVCacheDtype

__all__ = ["build_remediations"]

Compute = Callable[[CalcInput], CalcResult]

# Common context lengths, descending — we offer the largest that fits.
_CTX_LADDER = (131072, 65536, 32768, 16384, 8192, 4096, 2048, 1024)
_MAX_REMEDIATIONS = 4


def _fmt_ctx(ctx: int) -> str:
    return f"{ctx // 1024}k" if ctx % 1024 == 0 else str(ctx)


def build_remediations(
    inp: CalcInput, base: CalcResult, compute: Compute
) -> list[Remediation]:
    """Return up to four fitting single-lever fixes for a no-go configuration."""
    out: list[Remediation] = []
    seen: list[dict[str, int | str]] = []

    def try_add(label: str, delta: dict[str, int | str]) -> bool:
        if delta in seen:
            return False
        try:
            r = compute(inp.model_copy(update=delta))
        except InvalidParallelism:
            return False
        if not r.fits:
            return False
        seen.append(delta)
        out.append(
            Remediation(
                label=label,
                detail=f"fits — up to {r.max_concurrent} concurrent",
                delta=delta,
            )
        )
        return True

    # 1. FP8 KV cache — halves the KV footprint, keeps context and concurrency.
    if inp.kv_dtype != KVCacheDtype.FP8:
        try_add("FP8 KV cache", {"kv_dtype": KVCacheDtype.FP8.value})

    # 2. Reduce context — the largest common length below the current one that fits.
    for ctx in _CTX_LADDER:
        if ctx < inp.ctx_len and try_add(f"Context ≤ {_fmt_ctx(ctx)}", {"ctx_len": ctx}):
            break

    # 3. Higher TP / more GPUs — the smallest valid scale-up that fits.
    for factor in (2, 4, 8):
        cand = inp.tensor_parallel_size * factor
        if cand > inp.attention_heads or inp.attention_heads % cand != 0:
            continue
        if try_add(f"TP={cand} ({cand} GPUs)", {"tensor_parallel_size": cand, "gpu_count": cand}):
            break

    # 4. Reduce concurrency to the supported capacity (a guaranteed fit if any exists).
    if 1 <= base.max_concurrent < inp.max_seqs:
        try_add(f"Serve {base.max_concurrent} concurrent", {"max_seqs": base.max_concurrent})

    return out[:_MAX_REMEDIATIONS]
