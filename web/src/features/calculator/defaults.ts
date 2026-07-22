import type { CalcInput } from '../../api/types.ts'

/** The pre-computed default scenario shown on load (no blank state):
 *  Llama-3.3-70B, AWQ 4-bit, on 2× A100 80GB with TP=2. */
export const DEFAULT_INPUT: CalcInput = {
  model_ref: 'meta-llama/Llama-3.3-70B-Instruct',
  total_params: 70_600_000_000,
  layers: 80,
  attention_heads: 64,
  kv_heads: 8,
  head_dim: 128,
  hidden_size: 8192,
  attention_type: 'standard',
  weight_quant: 'awq-4bit',
  kv_dtype: 'fp16',
  ctx_len: 8192,
  max_seqs: 32,
  tensor_parallel_size: 2,
  gpu_count: 2,
  gpu_vram_gib: 80,
  gpu_memory_utilization: 0.9,
  max_num_batched_tokens: 2048,
  enforce_eager: false,
  max_num_seqs_cap: 256,
}

/** UI-only preset selection, kept out of the engine wire contract. `''` means
 *  no preset (the "— choose … —" placeholder); `'custom'` is an explicit custom
 *  pick; otherwise a preset id. Persisted in the URL so a shared/refreshed
 *  scenario shows the same dropdown selection it came from. */
export interface UiSelection {
  modelPresetId: string
  gpuPresetId: string
}

/** The preset selection matching DEFAULT_INPUT — keep the two in sync:
 *  Llama-3.3-70B (llama-3.3-70b) on an A100 80GB (a100-80gb). */
export const DEFAULT_SELECTION: UiSelection = {
  modelPresetId: 'llama-3.3-70b',
  gpuPresetId: 'a100-80gb',
}
