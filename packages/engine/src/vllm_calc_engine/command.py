"""Generate a runnable `vllm serve` command from a sizing config (Story 2.1).

Deterministic, pure, engine-owned so every surface (SPA/API/CLI) emits the
identical command (NFR3). Flags are only emitted when they carry meaning: full
-precision weights need no `--quantization`, and the default "auto" KV dtype
needs no `--kv-cache-dtype` — emitting them would be wrong or redundant.
"""

from vllm_calc_engine.models import CalcInput
from vllm_calc_engine.quantization import KVCacheDtype, WeightQuant

__all__ = ["serve_command"]

# Placeholder emitted when no model reference is known (custom models); the user
# swaps it for their HF repo id or local path.
_MODEL_PLACEHOLDER = "<your-model>"

# Mirrors CalcInput's default so `--max-num-batched-tokens` is emitted only when
# the user actually overrode it (kept in sync automatically).
_DEFAULT_MAX_BATCHED = CalcInput.model_fields["max_num_batched_tokens"].default

# WeightQuant → vLLM `--quantization` value. Full-precision schemes (fp32/fp16/
# bf16) and plain int8 have no single canonical serve flag, so they map to None
# (flag omitted) rather than emitting something vLLM would reject.
_QUANT_FLAG: dict[WeightQuant, str | None] = {
    WeightQuant.FP32: None,
    WeightQuant.FP16: None,
    WeightQuant.BF16: None,
    WeightQuant.INT8: None,
    WeightQuant.FP8: "fp8",
    WeightQuant.AWQ_4BIT: "awq",
    WeightQuant.GPTQ_4BIT: "gptq",
}

# KVCacheDtype → vLLM `--kv-cache-dtype` value. fp16/bf16 are the model default
# ("auto"), so the flag is omitted; only fp8 changes behaviour.
_KV_DTYPE_FLAG: dict[KVCacheDtype, str | None] = {
    KVCacheDtype.FP16: None,
    KVCacheDtype.BF16: None,
    KVCacheDtype.FP8: "fp8",
}


def serve_command(inp: CalcInput) -> str:
    """Return a single-line `vllm serve …` command matching the configuration."""
    parts: list[str] = ["vllm", "serve", inp.model_ref or _MODEL_PLACEHOLDER]
    parts += ["--tensor-parallel-size", str(inp.tensor_parallel_size)]

    quant = _QUANT_FLAG.get(inp.weight_quant)
    if quant is not None:
        parts += ["--quantization", quant]

    kv = _KV_DTYPE_FLAG.get(inp.kv_dtype)
    if kv is not None:
        parts += ["--kv-cache-dtype", kv]

    parts += ["--max-model-len", str(inp.ctx_len)]
    # `:g` drops trailing zeros: 0.9 → "0.9", 0.95 → "0.95".
    parts += ["--gpu-memory-utilization", f"{inp.gpu_memory_utilization:g}"]

    # Advanced overhead levers — only when they diverge from vLLM's defaults.
    if inp.max_num_batched_tokens != _DEFAULT_MAX_BATCHED:
        parts += ["--max-num-batched-tokens", str(inp.max_num_batched_tokens)]
    if inp.enforce_eager:
        parts.append("--enforce-eager")

    return " ".join(parts)
