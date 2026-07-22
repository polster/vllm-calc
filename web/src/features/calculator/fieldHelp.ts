/**
 * Plain-language, one-line descriptions for each calculator input field.
 * Copy is grounded in `spec.txt` (KEY INPUTS + the per-GPU formula notes) —
 * keep it accurate to the engine's behaviour, not aspirational.
 *
 * Keyed by the `CalcInput` field id so both the label and its tooltip stay
 * in sync from a single source.
 */
export const FIELD_HELP = {
  total_params:
    'Total parameter count of the model. For Mixture-of-Experts models use the TOTAL across all experts (all are resident), not the marketed active count.',
  layers:
    'Number of transformer layers (decoder blocks). The KV cache grows linearly with this.',
  attention_heads:
    'Number of attention (query) heads. Must divide evenly by the tensor-parallel size.',
  kv_heads:
    'Number of key/value heads (GQA/MQA). Fewer KV heads means a smaller KV cache — and this is where KV sharding stops (the replication wall).',
  head_dim:
    'Dimension of each attention head. Used with the KV heads and layers to size the KV cache per token.',
  hidden_size:
    'Model hidden dimension. Drives the activation-memory portion of overhead.',
  weight_quant:
    'Weight precision. Lower precision (e.g. AWQ / GPTQ 4-bit) shrinks the weights — and can shrink the KV cache too.',
  gpu_vram_gib:
    'Usable VRAM per GPU, in GiB (e.g. 80 for an A100-80GB). Pick a preset to fill this automatically.',
  gpu_count:
    'Number of GPUs in the node. In v1 this must equal the tensor-parallel size.',
  tensor_parallel_size:
    'How many GPUs the model is sharded across. Weights and KV divide by this; it must equal the GPU count and divide the head counts.',
  ctx_len:
    'Maximum sequence length (tokens) each request may use. The KV cache grows linearly with it.',
  max_seqs:
    'Requests you expect generating at the same time (in-flight sequences) — not total users; idle users don’t count. "Fits" means this is at most the GPU’s supported capacity.',
  gpu_memory_utilization:
    'Fraction of each GPU’s VRAM that vLLM may use (default 0.9). The rest is left as headroom.',
  kv_dtype:
    'Precision of the KV cache. FP8 roughly halves KV memory versus FP16 / BF16.',
  max_num_batched_tokens:
    'Chunked-prefill token budget per step (--max-num-batched-tokens). Bounds activation overhead — it is not the context length.',
  max_num_seqs_cap:
    'vLLM’s hard cap on concurrent sequences (--max-num-seqs, default 256). Caps the computed serving capacity.',
  enforce_eager:
    'Disable CUDA graphs. Frees ~0.5–2 GiB of overhead but can reduce throughput.',
} as const

export type FieldHelpKey = keyof typeof FIELD_HELP

/**
 * Help copy for the two preset pickers. These select local UI state (which
 * preset to auto-fill from) rather than a `CalcInput` field, so they live
 * beside FIELD_HELP instead of inside it — but still in this single file, so
 * all tooltip copy is edited in one place.
 */
export const PICKER_HELP = {
  model_preset:
    'Pick a known model to auto-fill its architecture below. Choose Custom to enter the values by hand.',
  gpu_preset:
    'Pick a GPU to auto-fill its usable VRAM. Choose Custom to enter a value by hand.',
} as const
