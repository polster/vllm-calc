---
stepsCompleted: [1, 2, 3, 4]
session_active: false
workflow_completed: true
ideas_generated: 15
inputDocuments: ['spec.txt']
session_topic: 'VRAM calculator for popular OSS LLMs — inputs for GPU/model presets, quantization, context length, tensor parallelism; visualizes required vs. available VRAM; extensible presets; generates the vllm serve command'
session_goals: 'Focus on the VRAM formula/model — identify every factor that drives GPU memory consumption (weights, KV cache, activations, framework overhead, quantization effects, TP/PP sharding, context length scaling) and how to model them accurately yet legibly.'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'Morphological Analysis', 'Assumption Reversal']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Simon
**Date:** 2026-07-01

## Session Overview

**Topic:** VRAM calculator for popular open-source LLMs. The app lets users provide inputs — GPU presets, model presets, quantization, context length, tensor parallelism — and visualizes the required VRAM, flagging when the selected GPU preset(s) are insufficient. Calculations are formula-driven. Users can add their own model and GPU presets. The app also generates the corresponding `vllm serve` command.

**Goals:** Focus on the **VRAM formula/model** — surface every factor that drives GPU memory consumption (model weights, KV cache, activations/runtime buffers, framework & CUDA overhead, quantization effects on both weights and KV cache, tensor/pipeline parallelism sharding, context-length and batch scaling) and figure out how to model them accurately while keeping the output legible to users.

### Session Setup

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Formula-driven VRAM calculator, focus on modeling every factor that drives GPU memory while staying legible.

**Recommended Techniques:**

- **First Principles Thinking (Phase 1):** Strip VRAM down to fundamental memory consumers, rebuilding the formula from physical truths rather than inherited blog-post heuristics.
- **Morphological Analysis (Phase 2):** Map every parameter that modulates each consumer (precision, weight/KV quant, context, batch/concurrency, TP/PP, overhead) into a parameter × consumer matrix — the skeleton of the calculation engine.
- **Assumption Reversal (Phase 3):** Adversarially flip the model's own assumptions to find where naive formulas lie, yielding correction factors, edge cases, and honest UI caveats.

**AI Rationale:** The problem is complex, abstract, and quantitative, calling for deep + structured techniques, with a creative first-principles opener to avoid anchoring on conventional but inaccurate formulas.

---

## Ideas Generated

### Phase 1 — First Principles Thinking: The VRAM Memory Inventory

**[Consumer #1]: Model Weights**
_Concept_: The static parameters, loaded once. The memory floor. Size = param_count × bytes_per_param (driven by quantization).
_Novelty_: Baseline — every calculator has this, but it's the anchor we build correction factors onto.

**[Consumer #2]: KV Cache**
_Concept_: Cached keys/values for every token in every active sequence, so attention doesn't recompute history. Dynamic — grows with tokens × concurrency. The true determinant of serving capacity.
_Novelty_: Most calculators under-model this by ignoring GQA, concurrency, and KV-cache quantization.

**[Consumer #3]: Activations**
_Concept_: Transient tensors during the forward pass — the working scratchpad for the in-flight batch.
_Novelty_: Scales with batch and hidden size; often lumped into a vague "overhead %."

**[Consumer #4]: Framework / CUDA Context Overhead**
_Concept_: Non-negotiable tax — CUDA context, kernels, cuBLAS/cuDNN workspaces.
_Novelty_: Roughly fixed per-GPU; commonly a flat ~1–2 GB reserve.

**[Consumer #5 — SHADOW]: vLLM Reserved Pool / `gpu_memory_utilization`**
_Concept_: vLLM pre-grabs ~0.9 × physical VRAM up front; the KV cache is paged in blocks inside that pool. Reframes the math from "fit in 80 GB" to "fit under 0.9 × 80 GB."
_Novelty_: Often omitted; it's *the* reason real-world "should fit" estimates OOM. **Decision: calculator targets `gpu_memory_utilization × VRAM` (default 0.9).**

**[Consumer #6 — SHADOW]: CUDA Graphs**
_Concept_: vLLM captures CUDA graphs for decode by default; captured graphs cost VRAM and scale with captured batch sizes. `enforce_eager` disables them to save memory at a latency cost.
_Novelty_: Rarely modeled; ties a UX toggle (eager vs. graphs) directly to a VRAM delta.

**[Consumer #7 — SHADOW]: Allocator Fragmentation Tax**
_Concept_: Reserved-but-unused blocks; real allocators never pack at 100%.
_Novelty_: Justifies an explicit headroom/safety factor rather than pretending math is exact.

**[Scope note]: Optimizer/Gradient state = ZERO (inference-only)**
_Concept_: Explicitly state the calculator assumes inference, so weights aren't multiplied by training's 3–4×.
_Novelty_: Honesty about scope prevents a whole class of confusion.

**First-principles formula skeleton:**
> `VRAM_required = Weights + KV_cache + Activations + Framework_overhead + CUDA_graphs`, and this must fit under `gpu_memory_utilization × physical_VRAM` (default 0.9).

### Phase 2 — Morphological Analysis: Simon's Draft Spec (spec.txt)

| Formula | What it tells you |
|---|---|
| `weights = params × bytes_per_param` | Raw VRAM floor for the model |
| `kv_per_token_per_layer = 2 × kv_heads × head_dim × kv_dtype_bytes` | KV cache growth rate (accounts for GQA) |
| `kv_total = kv_per_tok_layer × layers × ctx_len × max_seqs` | Total KV cache for a full batch |
| `overhead = weights × 5%` | Activations, CUDA kernels, fragmentation |
| `fits = (weights + kv + overhead) ≤ total_vram × gpu_util` | Go/no-go decision |
| `max_concurrent = ⌊free_kv_tokens / ctx_len⌋` | Real concurrent serving capacity |

**Tweakable inputs:** GPU preset (4090, A100, H100, H200, L40S…) or custom VRAM/count · Model preset (Llama 3.1/3.3, Mistral, Qwen, DeepSeek, Phi…) or custom architecture · Quantization (FP16 → AWQ/GPTQ 4-bit, affecting both weights and KV bytes) · Context length · max concurrent sequences · gpu_memory_utilization · Tensor parallelism (validates TP divides GPU count and KV heads). Also generates the `vllm serve` command. Possible extensions: speculative decoding, chunked prefill estimation, pipeline parallelism scheduling.

### Phase 3 — Assumption Reversal: Where the Draft Formula Lies

Five assumptions in the draft spec, ranked by real-world impact:

**🔴 #1 — `overhead = weights × 5%` is the weakest link. [RESOLVED — see below]**
_Problem_: Overhead does not scale with weights. For a 3B FP16 model, 5% = 0.3 GB — can't even cover the fixed CUDA context, so it under-estimates and wrongly reports "fits."

**🔴 #2 — `fits` check ignores tensor-parallel sharding. [RESOLVED — see below]**
_Problem_: Under TP=N, weights AND KV split across N GPUs. Real constraint is per-GPU: `(weights + kv)/TP + overhead_per_gpu ≤ vram_per_gpu × gpu_util`. TP must divide the memory, not just pass a validation check.

**🟠 #3 — MLA models break the KV formula entirely. [RESOLVED — descoped to generic, see below]**
_Problem_: DeepSeek-V2/V3 use Multi-head Latent Attention — caches a compressed latent, not `2 × kv_heads × head_dim`. Standard formula over-estimates DeepSeek KV by ~10×+. Model preset needs an **attention-type field** (MHA / GQA / MLA); KV term branches on it.

**🟠 #4 — `max_concurrent = ⌊free_kv_tokens / ctx_len⌋` assumes every sequence fills full context. [RESOLVED — see below]**
_Problem_: With PagedAttention a sequence only occupies blocks for tokens it has, so this is a conservative worst-case (label it as such). Also slightly circular with `max_seqs`, which already appears in `kv_total`. Decide: is `max_seqs` an input cap or an output of the KV budget?

**🟡 #5 — MoE weights must be TOTAL params, not active. [RESOLVED — see below]**
_Problem_: For MoE models (DeepSeek, Mixtral, Qwen-MoE), all experts are resident in VRAM. `params` must be total, not the marketed "active" count.

---

### RESOLVED — Rebuilt Overhead Model (Idea: three-mechanism decomposition)

Overhead is not one number — it's three mechanisms with three different scaling laws:

**① Fixed framework/CUDA context** — scales with *nothing*. CUDA context, kernels, cuBLAS/cuDNN workspaces + NCCL buffers (if TP>1). Roughly constant **per GPU**, ~1–2 GB (+~0.5 GB/GPU NCCL when TP>1). Independent of model size — this is why the 5% heuristic fails on small models.

**② Activations** — scale with *tokens-in-flight × hidden_size*, NOT weights. `≈ max_num_batched_tokens × hidden_size × dtype_bytes × k` (k = small single-digit multiplier for residual + MLP intermediate + attention buffers). Bounded by the **chunked-prefill token budget**, not context length. Typically a few hundred MB to ~1.5 GB.

**③ CUDA graphs** — semi-fixed chunk (~0.5–2 GB for larger models), ~0 with `enforce_eager=True`. A clean toggle → VRAM-delta for the UI.

> **overhead_per_gpu = fixed_context(~1–2 GB, +NCCL if TP>1) + activation(max_num_batched_tokens, hidden_size, dtype) + cuda_graphs(0 if eager)**

**Reframed `fits` check (matches how vLLM actually budgets, and sets up the TP fix):**
> `available_for_kv = gpu_util × vram_per_gpu − weights_per_gpu − overhead_per_gpu`
> `fits = required_kv_per_gpu ≤ available_for_kv`

**DECISION — UI granularity: Option (C) Hybrid.** Show one aggregate "overhead" number by default; let it expand to the three terms for power users. Turns overhead from a fudge factor into a teaching tool, and makes `max_num_batched_tokens` and `enforce_eager` into meaningful levers.

### RESOLVED — Tensor / Pipeline Parallelism Model

**Mechanism (TP):** slices *within* each layer (attention heads + MLP columns split across N GPUs).
- Weights shard cleanly: `weights_per_gpu ≈ weights_total / TP`.
- KV shards by KV heads: `kv_per_gpu ≈ kv_total / TP`.
- **Overhead does NOT shard — it multiplies:** each GPU pays its own fixed context (~1–2 GB) + activations + CUDA graphs, plus NCCL buffers that grow with TP. Scaling out buys memory room but taxes an overhead floor per GPU.
- Hard validation: `num_attention_heads % TP == 0` AND `num_kv_heads % TP == 0`.

**The KV-replication gotcha (key insight):** when `TP > num_kv_heads` (e.g. Llama-3-70B has only 8 KV heads), vLLM *replicates* KV heads — each GPU keeps ≥1 full head. So **KV per GPU stops shrinking once TP passes num_kv_heads**; effective divisor is `min(TP, num_kv_heads)`, not TP. Going TP=8→16 on Llama-70B does NOT halve KV — a naive `kv_total / TP` invents headroom that doesn't exist (fits ✅ → OOM trap).

**Pipeline Parallelism (the escape hatch):** splits *layers*, not tensors. `weights_per_gpu ≈ weights_total / PP`, `kv_per_gpu ≈ kv_total / PP`. No head-divisibility constraint (divides by layers) — the tool when TP can't divide heads or would hit the replication wall. Cost is a throughput "pipeline bubble," not VRAM.

**Unified per-GPU model:**
> `world_size = TP × PP` (must equal GPU count)
> `weights_per_gpu = weights_total / (TP × PP)`
> `kv_per_gpu = kv_total / (min(TP, num_kv_heads) × PP)`
> `overhead_per_gpu = fixed_context + NCCL(TP) + activation + cuda_graphs` *(paid on every GPU)*
> `fits = weights_per_gpu + kv_per_gpu + overhead_per_gpu ≤ gpu_util × vram_per_gpu`

**DECISION 1 — TP-only for v1.** Skip PP initially (simpler UI, covers ~90% of single-node setups). PP is a documented future extension for "won't divide" / multi-node cases.
**DECISION 2 — Actively warn on the replication wall.** When `TP > num_kv_heads`: "TP=N exceeds this model's K KV heads; KV won't shard further — consider fewer GPUs or (future) pipeline parallelism." Consistent with the teaching-tool philosophy.

### SCOPING DECISION — Keep the KV Calculation Generic (v1)

Explored attention-type branching (MHA/GQA/MQA all share `2 × kv_heads × head_dim`; MLA uses a compressed latent `(kv_lora_rank + qk_rope_head_dim)` — ~57× smaller for DeepSeek-V3) and sliding-window attention (Mistral/Gemma cap KV at `min(ctx_len, window)`). **Decision: do NOT branch in v1.**

_Rationale_: A single generic formula `2 × kv_heads × head_dim × kv_dtype_bytes × layers × ctx_len × max_seqs` **over-estimates** MLA and sliding-window models — and over-estimation is the *safe* direction for a sizing tool (user provisions enough, never OOMs). One formula erring conservative beats a pile of per-architecture branches.

_Handling_: MHA/GQA/MQA are exact (just different `kv_heads`). MLA & sliding-window are treated as **known conservative over-estimates** with a UI caveat ("estimate may be high for DeepSeek/MLA and sliding-window models") and logged as a **future refinement**, not v1 scope. (Footnote: vLLM's MLA has had materialized vs. native execution paths that change actual usage — another reason to defer precise MLA modeling.)

**Net v1 model = original spec.txt + the two fixes that change the go/no-go answer (real 3-term overhead + per-GPU TP sharding); everything else stays generic and simple.**

### RESOLVED — Capacity Framing (input vs. output) & the Headline Result

`max_seqs` and `max_concurrent` were conflated. Separate them:
- **`max_seqs`** = INPUT — what the user *wants* ("serve 32 concurrent").
- **`max_concurrent`** = OUTPUT — what the hardware *supports*, derived:
  > `available_for_kv = gpu_util × vram_per_gpu − weights_per_gpu − overhead_per_gpu`
  > `kv_tokens_capacity = available_for_kv / kv_bytes_per_token`  (per-GPU; ×TP for total)
  > `max_concurrent = min(max_num_seqs_cap, ⌊kv_tokens_capacity / ctx_len⌋)`

**DECISION — headline result is the sentence:** `fits ⟺ max_seqs ≤ max_concurrent` → e.g. *"You asked for 32; this GPU supports up to 47 ✅"* / *"...supports 47 ❌ — cut concurrency or context."* This is the tool's money output, not a bare boolean.
- **Worst-case label:** `max_concurrent` assumes every sequence fills full `ctx_len`; PagedAttention packs by actual tokens, so real capacity is usually higher. Label as conservative.
- **`max_num_seqs` cap:** vLLM caps the batch (default 256) even when KV allows more — hence the `min()`.

### RESOLVED — MoE Weights

**DECISION:** MoE presets store **TOTAL params** for the weights calc (all experts resident in VRAM). DeepSeek-V3 = 37B active but 671B total must be resident (getting this wrong under-counts ~18×). Active params matter for throughput, not memory — parked as an optional `active_params` field for future work. Nice-to-have: warn on a suspiciously low param count for a known-MoE preset.

---

## Idea Organization and Prioritization

### Thematic Organization

**Theme 1 — The Core Memory Model (rock-solid):** 7-part memory inventory (weights, KV cache, activations, framework/CUDA context, vLLM reserved pool, CUDA graphs, fragmentation); generic GQA-aware KV formula, exact for MHA/GQA/MQA; everything budgeted under `gpu_util × VRAM`; inference-only scope.

**Theme 2 — The Two Fixes That Change the Answer (breakthroughs):** (1) 3-term overhead model (fixed context + activations + CUDA graphs) replacing the broken `weights × 5%`, hybrid expandable UI; (2) per-GPU TP sharding with the `min(TP, kv_heads)` KV-replication wall + active warning.

**Theme 3 — Legibility & Honesty (trust):** headline result as a sentence (`fits ⟺ max_seqs ≤ max_concurrent`); conservative worst-case labeling; generic over-estimate accepted for MLA/sliding-window; MoE total-params correctness.

**Theme 4 — Deliberately Deferred (scope discipline):** MLA/sliding-window branching, pipeline parallelism, speculative decoding, chunked-prefill precision, throughput/active-params modeling.

### Final v1 Formula Set

```
# Per-GPU model (TP-only for v1)
weights_total       = params × bytes_per_param            # MoE: params = TOTAL, not active
kv_bytes_per_token  = 2 × kv_heads × head_dim × kv_dtype_bytes × layers   # GQA-aware
weights_per_gpu     = weights_total / TP
kv_per_gpu(seqs)    = kv_bytes_per_token × ctx_len × seqs / min(TP, kv_heads)
overhead_per_gpu    = fixed_context(~1–2 GB, +NCCL if TP>1)
                      + activation(max_num_batched_tokens, hidden_size, dtype)
                      + cuda_graphs(0 if enforce_eager)

available_for_kv    = gpu_util × vram_per_gpu − weights_per_gpu − overhead_per_gpu
max_concurrent      = min(max_num_seqs_cap, ⌊(available_for_kv / kv_bytes_per_token) / ctx_len⌋)

# Headline result:
fits  ⟺  max_seqs ≤ max_concurrent

# Validation: num_attention_heads % TP == 0 AND num_kv_heads % TP == 0;  TP == gpu_count
# Warn: if TP > num_kv_heads → KV won't shard further
# Caveat: over-estimates MLA (DeepSeek) & sliding-window (Mistral/Gemma) models — conservative/safe
```

### Prioritized Action Plan

1. **🥇 Update `spec.txt`** with the corrected 3-term overhead, per-GPU TP sharding, and the input/output `max_seqs → max_concurrent` framing. *(These are the changes that affect correctness.)*
2. **🥈 Define preset schemas** — Model preset: `params (total), layers, kv_heads, head_dim, hidden_size, attention_type, is_moe, [active_params]`. GPU preset: `vram_per_gpu, count`. The data foundation for the calculator.
3. **🥉 Hand to Winston (architect)** to turn this model into a solution design: calc engine, preset store, visualization, `vllm serve` command generation.

## Session Summary and Insights

**Key Achievements:**
- Hardened a working draft formula into a defensible v1 model via First Principles → Morphological → Assumption Reversal.
- Fixed the two bugs that flip a "fits ✅" into a real-world OOM: the `weights × 5%` overhead fallacy and the missing per-GPU TP sharding.
- Discovered non-obvious traps: the KV-replication wall (`min(TP, kv_heads)`), MLA's ~57× KV compression, sliding-window's context cap, and MoE total-vs-active params.
- Reframed the output from a bare boolean into a legible capacity sentence.

**Session Reflections:** The user arrived with an unusually strong, concrete draft (`spec.txt`) — the highest leverage was adversarial scrutiny (Phase 3), not idea generation. A key judgment call was consciously *descoping* per-architecture precision (MLA/SWA) in favor of a generic, conservatively-over-estimating formula — the right altitude for a sizing tool. Scope discipline was as valuable as the modeling itself.

---

_Session complete._ ✅
