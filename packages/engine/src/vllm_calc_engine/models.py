"""Shared Pydantic I/O models — the engine-owned contract.

These are imported by the API and CLI; they are defined here and nowhere else,
so all surfaces speak the same shapes (parity, NFR3). Memory quantities are in
integer bytes; GiB conversion happens only at presentation edges. GPU VRAM is
accepted as human-facing GiB on input (a single documented input-edge conversion).
"""

from pydantic import BaseModel, Field

from vllm_calc_engine.quantization import KVCacheDtype, WeightQuant

__all__ = ["CalcInput", "Breakdown", "CalcResult"]


class CalcInput(BaseModel):
    """A full sizing request: model architecture + GPU + workload + advanced levers."""

    # Model architecture
    total_params: int = Field(gt=0, description="Total params (MoE: all experts).")
    layers: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    kv_heads: int = Field(gt=0)
    head_dim: int = Field(gt=0)
    hidden_size: int = Field(gt=0)

    # Precision
    weight_quant: WeightQuant
    kv_dtype: KVCacheDtype

    # Workload
    ctx_len: int = Field(gt=0)
    max_seqs: int = Field(gt=0, description="Desired concurrent sequences.")

    # GPU & parallelism
    tensor_parallel_size: int = Field(gt=0)
    gpu_count: int = Field(gt=0)
    gpu_vram_gib: float = Field(gt=0, description="Physical VRAM per GPU, in GiB.")
    gpu_memory_utilization: float = Field(default=0.9, gt=0, le=1)

    # Advanced overhead levers
    max_num_batched_tokens: int = Field(default=2048, gt=0)
    enforce_eager: bool = False
    max_num_seqs_cap: int = Field(default=256, gt=0, description="vLLM batch cap.")


class Breakdown(BaseModel):
    """Per-GPU memory breakdown, in integer bytes (for 'show your work')."""

    weights_per_gpu_bytes: int
    kv_per_gpu_bytes: int  # for the requested max_seqs at full ctx_len
    overhead_fixed_context_bytes: int
    overhead_activations_bytes: int
    overhead_cuda_graphs_bytes: int
    overhead_total_bytes: int
    used_per_gpu_bytes: int  # weights + overhead + kv (requested)
    budget_per_gpu_bytes: int  # gpu_memory_utilization × physical VRAM
    available_for_kv_bytes: int  # budget − weights − overhead


class CalcResult(BaseModel):
    """The headline answer: verdict, capacity, breakdown, honesty labels."""

    fits: bool
    requested_max_seqs: int
    max_concurrent: int
    verdict: str
    worst_case_note: str
    supported_vllm_range: str
    warnings: list[str]
    breakdown: Breakdown
