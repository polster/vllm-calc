"""Golden tests for `vllm serve` command generation (Story 2.1).

The command is derived deterministically from CalcInput and must match the flags
vLLM would actually accept: full-precision weights emit no --quantization, an
"auto" KV dtype emits no --kv-cache-dtype, and a missing model reference falls
back to a copy-and-replace placeholder rather than a wrong repo id.
"""

from vllm_calc_engine.command import serve_command
from vllm_calc_engine.models import CalcInput
from vllm_calc_engine.quantization import KVCacheDtype, WeightQuant

BASE = CalcInput(
    total_params=70_000_000_000,
    layers=80,
    attention_heads=64,
    kv_heads=8,
    head_dim=128,
    hidden_size=8192,
    weight_quant=WeightQuant.AWQ_4BIT,
    kv_dtype=KVCacheDtype.FP16,
    ctx_len=8192,
    max_seqs=32,
    tensor_parallel_size=2,
    gpu_count=2,
    gpu_vram_gib=80,
    gpu_memory_utilization=0.9,
)


def test_golden_awq_command_omits_auto_kv_dtype() -> None:
    cmd = serve_command(BASE)
    assert cmd == (
        "vllm serve <your-model> "
        "--tensor-parallel-size 2 "
        "--quantization awq "
        "--max-model-len 8192 "
        "--gpu-memory-utilization 0.9"
    )


def test_uses_model_ref_when_present() -> None:
    cmd = serve_command(BASE.model_copy(update={"model_ref": "meta-llama/Llama-3.3-70B-Instruct"}))
    assert cmd.startswith("vllm serve meta-llama/Llama-3.3-70B-Instruct ")


def test_full_precision_weights_emit_no_quantization_flag() -> None:
    cmd = serve_command(BASE.model_copy(update={"weight_quant": WeightQuant.FP16}))
    assert "--quantization" not in cmd


def test_gptq_maps_to_gptq() -> None:
    cmd = serve_command(BASE.model_copy(update={"weight_quant": WeightQuant.GPTQ_4BIT}))
    assert "--quantization gptq" in cmd


def test_fp8_kv_cache_adds_kv_dtype_flag() -> None:
    cmd = serve_command(BASE.model_copy(update={"kv_dtype": KVCacheDtype.FP8}))
    assert "--kv-cache-dtype fp8" in cmd


def test_gpu_memory_utilization_formatted_without_trailing_zeros() -> None:
    cmd = serve_command(BASE.model_copy(update={"gpu_memory_utilization": 0.95}))
    assert "--gpu-memory-utilization 0.95" in cmd


def test_calculate_result_carries_the_command() -> None:
    from vllm_calc_engine.calculate import calculate

    r = calculate(BASE)
    assert r.serve_command == serve_command(BASE)
    assert r.serve_command.startswith("vllm serve ")
