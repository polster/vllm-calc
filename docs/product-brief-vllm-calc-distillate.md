---
title: "Product Brief Distillate: vllm-calc"
type: llm-distillate
source: "product-brief-vllm-calc.md"
created: "2026-07-06"
purpose: "Token-efficient context for downstream PRD creation"
---

# vllm-calc — Detail Pack

Companion to `product-brief-vllm-calc.md`. Also see `spec.txt` (v1 formula set) and `docs/brainstorming/brainstorming-session-2026-07-01.md` (full modeling rationale).

## Product in one line
Free, open-source, browser-based VRAM calculator that answers "will this OSS LLM fit on my GPUs under vLLM?" — visualizes per-GPU VRAM, gives a go/no-go capacity verdict, suggests the nearest fitting config, and generates the runnable `vllm serve` command.

## Positioning / strategic decisions (settled)
- **Audience:** public/OSS tool. v1 **optimizes for the multi-GPU serving engineer** (70B/MoE across 2–8 GPUs) — sharpest pain + sharpest differentiation. Solo-GPU users, cost planners, and newcomers are *served but not optimized-for*.
- **Hero value:** avoid OOM / right-size fast — kill the launch-and-crash + guess-and-retry loop.
- **The moat is ACCURACY, not command-generation.** A competitor (WireUnwired) already generates a vLLM command → command-gen is table stakes done more correctly. Differentiation = vLLM-accurate 3-term overhead + real per-GPU TP sharding + GQA-aware KV, all made *provable and legible*.

## Requirements hints (from discovery — candidates for PRD functional reqs)
- **Inputs:** GPU preset (4090/A100/H100/H200/L40S…) or custom (vram_per_gpu, count); model preset (Llama 3.x, Mistral, Qwen, DeepSeek, Phi…) or custom architecture; quantization (FP16→AWQ/GPTQ 4-bit); context length; concurrency (max_seqs); gpu_memory_utilization (default 0.9); tensor-parallel size; advanced levers (max_num_batched_tokens, enforce_eager).
- **Model preset schema:** params (TOTAL, incl. all MoE experts), layers, kv_heads, head_dim, hidden_size, is_moe, [active_params optional/future]. GPU preset schema: vram_per_gpu, count.
- **Outputs:** per-GPU VRAM breakdown viz (weights / KV / overhead vs. gpu_util × vram_per_gpu); headline capacity sentence (`fits ⟺ max_seqs ≤ max_concurrent`, e.g. "asked 32; supports 47 ✅"); nearest-fitting-config remediation on no-go; generated `vllm serve` command matching the computed fit.
- **User-added custom presets** for both models and GPUs.
- **UI granularity:** overhead shown as one aggregate number by default, expandable to its 3 terms (teaching-tool behavior).
- **Warnings/labels:** KV-replication-wall warning when TP > num_kv_heads; "conservative — assumes full-context per sequence" label on max_concurrent; "over-provisioned estimate" flag on MLA/sliding-window models.

## Technical context (the v1 model — full detail in spec.txt)
- **Core:** `VRAM = weights + KV + overhead`, must fit under `gpu_util × vram_per_gpu`, inference-only. Errs conservative (over-estimate = safe).
- **Weights:** `params × bytes_per_param`. MoE = TOTAL params (all experts resident); marketed "active" params are throughput-only, NOT memory. Getting this wrong under-counts ~18× (DeepSeek-V3: 37B active / 671B total).
- **KV cache (generic, GQA-aware):** `2 × kv_heads × head_dim × kv_dtype_bytes × layers × ctx_len × max_seqs`. MHA/GQA/MQA all covered by varying kv_heads (exact). Quantization affects kv_dtype_bytes.
- **Overhead = 3 mechanisms, 3 scaling laws (NOT `weights × 5%`):** (1) fixed CUDA context ~1–2 GB/GPU (+~0.5 GB/GPU NCCL if TP>1), scales with nothing; (2) activations ≈ max_num_batched_tokens × hidden_size × dtype × k, bounded by chunked-prefill budget not ctx_len (~few hundred MB–1.5 GB); (3) CUDA graphs ~0.5–2 GB, =0 if enforce_eager.
- **Tensor parallelism (per-GPU):** `weights_per_gpu = weights_total/TP`; `kv_per_gpu = kv_total / (min(TP, kv_heads))`; overhead does NOT shard — paid per GPU. Validation: num_attention_heads % TP == 0 AND num_kv_heads % TP == 0; TP == gpu_count.
- **KV-replication wall (key gotcha):** when TP > num_kv_heads, vLLM replicates KV heads → per-GPU KV stops shrinking (effective divisor min(TP, kv_heads)). Naive kv_total/TP invents non-existent headroom → "fits ✅"→OOM.
- **Capacity (input vs output):** max_seqs = INPUT (what user wants); max_concurrent = OUTPUT = `min(max_num_seqs_cap(default 256), ⌊(available_for_kv / kv_bytes_per_token) / ctx_len⌋)` where `available_for_kv = gpu_util × vram_per_gpu − weights_per_gpu − overhead_per_gpu`.
- **Accuracy target:** ±10% vs. actual `vllm serve` startup reserve, biased to over-predict. Requires a **validation harness** (launch real configs, compare predicted vs. reserved bytes), pinned to a stated vLLM version range. Frame as calibrated estimate w/ headroom, NOT an absolute never-OOM guarantee; document failure modes (version drift, driver/fragmentation, coexisting processes).

## Rejected / deferred (do NOT re-propose for v1)
- **MLA exact KV math (DeepSeek-V2/V3):** compressed latent `(kv_lora_rank + qk_rope_head_dim)`, no ×2/×heads — ~57× smaller than naive. Deferred to **fast-follow #1** (competitive parity vs. llmvramcalculator + land-grab). v1 = conservative over-estimate + UI flag. (Caveat: vLLM has had materialized vs. native MLA execution paths that change actual usage.)
- **Sliding-window attention (Mistral/Gemma):** KV capped at `min(ctx_len, window)`. Deferred; v1 over-estimates + flags.
- **Pipeline parallelism:** splits layers (divides weights & KV by PP, no head-divisibility constraint). v1 is TP-only. Deferred.
- **Deferred also:** speculative decoding, chunked-prefill precision, throughput/latency modeling, cost/$ modeling.
- **Committed fast-follow order:** (1) exact MLA math; (2) URL-encoded shareable scenarios; (3) HF config.json auto-ingest.

## Competitive intelligence (from web research 2026-07-05)
- **No single tool combines** vLLM-accurate 3-term overhead + real per-GPU TP sharding + GQA/MLA KV + runnable `vllm serve` command. That intersection is the defensible position.
- **HF accelerate "Model Memory Usage"** (huggingface.co/spaces/hf-accelerate/model-memory-usage): weights-only + flat +20% inference fudge; ignores KV/context/GQA/TP. Not a serving tool.
- **NyxKrage LLM-Model-VRAM-Calculator:** local/GGUF/EXL2 single-GPU hobbyist; no TP/vLLM/command.
- **oobabooga / DavidAU GGUF calculators:** llama.cpp-only; irrelevant to vLLM's safetensors+AWQ/GPTQ/FP8 world.
- **ApXML "Can You Run This LLM?"** (apxml.com/tools/vram-calculator): KV + KV-quant + GPU qty + low concurrency (≤8); no TP, opaque method, no command.
- **llmvramcalculator.com** — most accurate competitor: GQA + DeepSeek MLA + GGUF K-quant + TP as *naive linear scaling*; NO command; "theoretical," ignores framework optimizations.
- **SelfHostLLM** (selfhostllm.org, OSS github.com/erans/selfhostllm): models concurrency (avail mem ÷ KV-per-request) but worst-case only; no TP; no command.
- **WireUnwired** (wireunwired.com/local-llm-vram-calculator): the KEY competitor to beat — simulates vLLM/PagedAttention AND generates a command, handles MoE/vision/FP8 — BUT appears to skip TP and GQA, uses outdated `python -m vllm` (not `vllm serve`), undisclosed accuracy model.
- **vLLM itself:** no official pre-flight "will it fit?" tool — you launch to find out. Documented unmet demand: vllm-project/vllm#22291 asks how to compute --gpu-memory-utilization for target concurrency.
- **Unconfirmed:** could not verify an "Alexander Smirnov" calculator or a distinct vast.ai VRAM estimator — treat as non-existent unless found.

## Trends making it timely
- GQA now standard (Llama 3.1 70B: 64 query / 8 KV heads → ~8× KV reduction); MLA spreading (DeepSeek) → naive KV math increasingly wrong.
- Quantization diversity mainstream in vLLM (AWQ/GPTQ/FP8 + KV-cache quant); GGUF/EXL2-only tools miss the vLLM audience.
- Long context (128k–256k+) makes KV — not weights — the binding constraint (defeats weights-only tools).
- Multi-GPU default for 70B+/MoE → TP sizing help is real unmet demand.

## Open questions (unresolved — for PRD/architecture)
- Exact `k` multiplier and formula for the activation overhead term (needs empirical calibration via the validation harness).
- Precise fixed-context + NCCL constants per GPU arch / vLLM version.
- How to keep curated presets current as models ship weekly (CI check vs. HF config.json? ownership/trust model?) — crowdsourced presets risk silent rot that poisons the accuracy moat.
- Distribution/discovery plan for an OSS tool (SEO on "<model> vram" / "vllm OOM", r/LocalLLaMA, HN, vLLM Discord) — not yet addressed.
- Web-only for v1, or also a headless CLI/library (`vllm-calc check`, exit 1 on no-go) for CI pre-flight? (Opportunity surfaced; not committed.)
- Cost/$ layer mapping GPU count → cloud instance SKUs (serves the cost-planner segment; currently out of scope).
- Tech stack unchosen (implied browser/web app; framework TBD).

## Scope signals summary
- **IN v1:** core memory model (weights + GQA KV + 3-term overhead); per-GPU TP + replication warning; nearest-fitting-config remediation; curated ~15–20 model + common GPU presets (correctness-first) + custom presets; VRAM viz + capacity sentence; `vllm serve` gen; quantization (weights+KV); MoE total-params; validation harness + ±10% accuracy target.
- **OUT v1 (flagged in UI where relevant):** MLA/SWA exact KV; pipeline parallelism; spec decoding; chunked-prefill precision; throughput/latency; cost.
