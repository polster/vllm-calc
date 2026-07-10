/** Wire types mirroring the engine's Pydantic contract (snake_case on the wire).
 *  Kept in sync with packages/engine/src/vllm_calc_engine/models.py. */

export type WeightQuant = 'fp32' | 'fp16' | 'bf16' | 'fp8' | 'int8' | 'awq-4bit' | 'gptq-4bit'
export type KVDtype = 'fp16' | 'bf16' | 'fp8'
export type AttentionType = 'standard' | 'mla' | 'sliding_window' | 'other'

export interface CalcInput {
  model_ref?: string | null
  total_params: number
  layers: number
  attention_heads: number
  kv_heads: number
  head_dim: number
  hidden_size: number
  attention_type: AttentionType
  weight_quant: WeightQuant
  kv_dtype: KVDtype
  ctx_len: number
  max_seqs: number
  tensor_parallel_size: number
  gpu_count: number
  gpu_vram_gib: number
  gpu_memory_utilization: number
  max_num_batched_tokens: number
  enforce_eager: boolean
  max_num_seqs_cap: number
}

export interface Breakdown {
  weights_per_gpu_bytes: number
  kv_per_gpu_bytes: number
  overhead_fixed_context_bytes: number
  overhead_activations_bytes: number
  overhead_cuda_graphs_bytes: number
  overhead_total_bytes: number
  used_per_gpu_bytes: number
  budget_per_gpu_bytes: number
  available_for_kv_bytes: number
}

export interface Remediation {
  label: string
  detail: string
  delta: Partial<CalcInput>
}

export interface Flag {
  type: string
  message: string
}

export interface CalcResult {
  fits: boolean
  requested_max_seqs: number
  max_concurrent: number
  verdict: string
  worst_case_note: string
  supported_vllm_range: string
  warnings: string[]
  breakdown: Breakdown
  serve_command: string
  remediations: Remediation[]
  flags: Flag[]
}

export interface ModelPreset {
  id: string
  name: string
  total_params: number
  layers: number
  attention_heads: number
  kv_heads: number
  head_dim: number
  hidden_size: number
  is_moe: boolean
  attention_type: AttentionType
  source: string
  last_verified: string
  vllm_version_checked: string
}

export interface GpuPreset {
  id: string
  name: string
  vram_gib: number
  source: string
  last_verified: string
  vllm_version_checked: string
}

/** Structured error contract: {error:{type,message,details?}}. */
export interface ApiErrorBody {
  type: string
  message: string
  details?: unknown
}
