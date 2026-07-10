import type { CalcInput } from '../../api/types.ts'

/** The pre-computed default scenario shown on load (no blank state):
 *  Llama-3.3-70B, AWQ 4-bit, on 2× A100 80GB with TP=2. */
export const DEFAULT_INPUT: CalcInput = {
  total_params: 70_600_000_000,
  layers: 80,
  attention_heads: 64,
  kv_heads: 8,
  head_dim: 128,
  hidden_size: 8192,
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
