---
title: 'Add Kimi K3 model preset'
type: 'feature'
created: '2026-08-07'
status: 'done'
route: 'one-shot'
---

# Add Kimi K3 model preset

## Intent

**Problem:** Moonshot AI's newly released Kimi K3 (2.8T-param hybrid-attention MoE, released 2026-07-27) wasn't available as a model choice in the calculator.

**Approach:** Add `presets/models/kimi-k3.yaml` per the existing no-code preset-contribution process (`CONTRIBUTING.md`), sourcing every architecture number from the model's live Hugging Face `config.json` / API metadata rather than marketing copy. Kimi K3's real architecture is a genuine hybrid — 69 of 93 layers use KDA (linear/recurrent attention, no growing per-token KV cache) and 24 use Gated MLA (real latent KV cache) — which doesn't cleanly fit `standard`/`mla`/`sliding_window`, so `attention_type: other` was used to honestly flag the KV-cache estimate as uncalibrated (per `packages/engine/src/vllm_calc_engine/flags.py`) rather than assert a confident but wrong number.

## Suggested Review Order

- New preset; `total_params` (2,779,931,837,184) verified against HF safetensors metadata (all-experts, not the ~104B active figure), `attention_type: other` chosen deliberately over `mla` given the hybrid KDA/MLA architecture.
  [`kimi-k3.yaml`](../presets/models/kimi-k3.yaml)
