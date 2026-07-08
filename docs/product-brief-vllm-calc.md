---
title: "Product Brief: vllm-calc"
status: "complete"
created: "2026-07-05"
updated: "2026-07-05"
inputs:
  - spec.txt
  - docs/brainstorming/brainstorming-session-2026-07-01.md
  - web research (competitive landscape, 2026-07-05)
---

# Product Brief: vllm-calc

## Executive Summary

**vllm-calc** is a free, open-source VRAM calculator that answers the one question every engineer asks before serving an open-source LLM with vLLM: *"Will this actually fit on my GPUs?"* You pick a GPU, a model, a quantization, a context length, and a tensor-parallel size — and it tells you, before you launch anything, whether the configuration fits, how many concurrent requests it can serve, and the exact `vllm serve` command to run it.

Today, engineers find out whether a model fits by launching it and waiting for the out-of-memory crash — then guessing at `--gpu-memory-utilization`, context length, or GPU count and trying again. There's no widely-adopted pre-flight "will it fit?" tool that models what vLLM actually does; you discover the answer the hard way. The existing web calculators don't close the gap: they're built for single-GPU llama.cpp/GGUF hobbyists, they model inference overhead as a flat "+20%" fudge factor, and the few that target vLLM ignore tensor parallelism and grouped-query attention entirely.

vllm-calc wins on **accuracy where it counts**. It models what vLLM actually reserves — model weights, a transparent three-part overhead term, and a GQA-aware KV cache — and it does the real per-GPU tensor-parallel math that determines fit on multi-GPU boxes. It errs conservative by design, so "fits" never becomes a 2 a.m. OOM. And it turns the answer into something you can act on: a copy-paste-ready `vllm serve` command.

## The Problem

Standing up an LLM on vLLM is a trial-and-error memory game. An engineer picks a 70B model, launches `vllm serve`, and hits a CUDA OOM. Was it the context length? The KV cache? Do they need tensor parallelism across two GPUs, or four? Is `--gpu-memory-utilization 0.9` too aggressive? Each guess costs a model reload — minutes of waiting — and the failure modes are opaque. The pain is worst exactly where the stakes are highest: large models, long context, and multi-GPU serving, where the interactions between weights, KV cache, and parallelism are hardest to reason about by hand.

The cost of the status quo: wasted engineering hours, over-provisioned (expensive) GPU rentals bought "to be safe," under-provisioned deployments that fail under load, and a real barrier to entry for teams new to vLLM. There is documented, unmet demand — vLLM's own issue tracker carries requests for exactly this kind of sizing help.

## The Solution

vllm-calc is a browser-based calculator (no install, nothing to run) built around a single, legible answer. The user selects:

- a **GPU preset** (4090, A100, H100, H200, L40S…) or a custom VRAM/count,
- a **model preset** (Llama 3.x, Mistral, Qwen, DeepSeek, Phi…) or custom architecture,
- **quantization** (FP16 → AWQ/GPTQ 4-bit — affecting both weights and KV cache),
- **context length**, **concurrency**, **gpu_memory_utilization**, and **tensor-parallel size**.

It then visualizes the per-GPU VRAM breakdown — weights, KV cache, and overhead — against the usable budget, and delivers the headline verdict as a plain sentence: *"You asked for 32 concurrent requests; this setup supports up to 47 ✅"* — or a clear ❌. Crucially, on a no-go it doesn't just say no: it suggests the **nearest fitting configuration** ("won't fit at 128k context; fits at 90k — or at FP8, or at TP=8"), killing the config-retry loop, not just the launch-retry loop. Users can add their own model and GPU presets. Finally, it generates the ready-to-run `vllm serve` command with the flags that match the computed fit.

## What Makes This Different

The market is full of single-GPU, framework-agnostic, number-only calculators. vllm-calc occupies an intersection **no existing tool fills**:

- **vLLM-accurate memory model.** Reproduces vLLM's real partition — weights + KV + overhead under the `gpu_memory_utilization` cap — instead of a generic estimate. The overhead term is a transparent three-part breakdown (fixed CUDA context + activations + CUDA graphs), not the industry-standard "+20%" fudge.
- **Real per-GPU tensor-parallel math.** Shards weights and KV across GPUs while correctly replicating per-GPU overhead — and warns at the KV-replication wall (when TP exceeds a model's KV-head count). Competitors either ignore TP or scale it naively.
- **GQA-aware KV cache.** Uses actual KV-head counts, so modern models (Llama 3, Qwen2, Mistral) are modeled correctly — where naive calculators are increasingly wrong.
- **Actionable output.** A modern `vllm serve` command, correct to the computed configuration.

Because accuracy is the moat, it has to be **provable, not asserted**. vllm-calc is calibrated against a validation harness that launches real `vllm serve` configurations and compares predicted vs. actually-reserved VRAM, pinned to a stated vLLM version range — and the tool shows its work (the weights/KV/overhead breakdown users can check against vLLM's own startup logs). Making the accuracy *legible at the point of use* is what turns a "more accurate number" into trust.

Honest read on the moat: one competitor already generates a vLLM command, so *command generation is table stakes we simply do more correctly*. **Accuracy is the differentiator** — transparent overhead, real TP sharding, GQA-awareness — and it compounds with being open source and community-extensible.

## Who This Serves

**Primary (v1 optimizes for this persona):** the **multi-GPU serving engineer** — an ML/platform engineer standing up a 70B or MoE model across 2–8 GPUs on vLLM. This is where the pain is sharpest (tensor-parallel interactions are hardest to reason about by hand) and where vllm-calc's differentiation — real per-GPU TP sharding — matters most. Success for them: they configure a multi-GPU deployment once, it fits, and it serves the concurrency they expected.

**Secondary (served, not optimized-for):** solo engineers on a single rented GPU; teams doing hardware/cost planning; and newcomers — for whom the transparent weights/KV/overhead breakdown *teaches why VRAM is consumed* as a natural side effect of the primary UI, rather than a separate mode.

## Success Criteria

- **Accuracy (the core metric):** on a published validation suite of real GPU × model × TP configurations, predicted VRAM lands within **±10%** of what `vllm serve` actually reserves at startup, biased to over-predict (a small safety margin) rather than under-predict. Framed honestly as a *calibrated estimate with headroom*, not an absolute never-OOM guarantee — with known failure modes (vLLM version drift, driver/fragmentation, coexisting processes) documented.
- **Trust/adoption:** validation-suite pass rate published and green; growth in curated + community presets; inbound references from vLLM/HF community discussions; shared-scenario link opens as a distribution signal. (GitHub stars are a coarse proxy, not the goal.)
- **Usefulness:** opt-in "did it fit?" feedback after a real launch; qualitative signal that the tool replaced the launch-and-crash loop.

## Scope

**In (v1):** the core memory model (weights + GQA-aware KV + three-part overhead); per-GPU **tensor parallelism** with the KV-replication warning; **"nearest fitting config" remediation** on a no-go; a **curated, validated baseline** of the top ~15–20 models and common GPUs (correctness first) plus user-added custom presets; VRAM visualization and the go/no-go capacity sentence; `vllm serve` command generation; quantization affecting weights and KV; MoE total-parameter handling.

**Out (deferred):** per-architecture KV precision for MLA (DeepSeek) and sliding-window (Mistral/Gemma) models — intentionally left as conservative over-estimates for v1, but **flagged in the UI as "over-provisioned estimate"** so the number isn't silently misleading; pipeline parallelism; speculative decoding; chunked-prefill precision; throughput/latency modeling.

**Committed fast-follows (post-v1, in order):** (1) **exact MLA KV math** — the first fast-follow, both competitive parity and a differentiation land-grab on the highest-interest models; (2) **URL-encoded shareable scenarios** for distribution; (3) **HF `config.json` auto-ingest** so custom models don't require hand-entering architecture params.

## Vision

If vllm-calc succeeds, it becomes the **default pre-flight step for vLLM deployment** — the tool people reach for before they touch a GPU, and the answer they trust because it matches reality. From an accurate sizing calculator it can grow into a broader serving-planning companion: throughput and cost estimation, multi-node pipeline parallelism, architecture-exact modeling for MLA and sliding-window models, and tight integration with model hubs so any model is one click from a validated, runnable serving config. The north star: nobody's first experience of a new model should be an out-of-memory crash.
