---
title: 'Add GLM-5.2 model preset'
type: 'feature'
created: '2026-09-07'
status: 'done'
route: 'one-shot'
---

# Add GLM-5.2 model preset

## Intent

**Problem:** Zhipu AI (Z.ai) released GLM-5.2 (June 2026, ~753B-param MoE, MIT license, 1M-token context) and it wasn't available as a model choice in the calculator.

**Approach:** Add `presets/models/glm-5.2.yaml` per the existing no-code preset-contribution process (`CONTRIBUTING.md`), sourcing every architecture number from the model's Hugging Face `config.json` (`zai-org/GLM-5.2`, `model_type: glm_moe_dsa`) and safetensors metadata rather than marketing copy. GLM-5.2's attention is MLA-style (qk_nope_head_dim 192 + qk_rope_head_dim 64 → `head_dim: 256`) layered with a novel sparse "IndexShare" token-selection indexer whose own memory cost this codebase has never modeled or verified. Because Zhipu gave this mechanism its own distinct `model_type` rather than reusing DeepSeek's, and because the repo's honesty rule reserves `attention_type: mla` for architectures it can confidently calibrate, `attention_type: other` was used — same call as the Kimi K3 precedent — to honestly flag the KV-cache estimate as uncalibrated instead of asserting a confident but unverified "MLA-conservative" claim.

## Suggested Review Order

- New preset; `total_params` (753,329,940,480) verified against HF safetensors metadata (all-weights, matches the model card's "753B" figure), `attention_type: other` chosen deliberately over `mla` despite the underlying MLA-style KV decomposition, because of the unmodeled sparse-indexer mechanism — flagged in review as a judgment call worth a second look.
  [`glm-5.2.yaml`](../presets/models/glm-5.2.yaml)
- One pre-existing, out-of-scope issue surfaced by review and deferred rather than fixed here: the engine's `SUPPORTED_VLLM_RANGE` (`0.13`–`<0.14`) is now well behind this preset's real `vllm_version_checked: "0.23"` (GLM-5.2's actual minimum vLLM requirement).
  [`deferred-work.md`](../docs/deferred-work.md#engines-supported_vllm_range-is-stale-relative-to-newer-presets-vllm_version_checked)

  **Correction (2026-09-07):** the premise above was wrong — `vllm_version_checked` is project-baseline provenance, not a per-model minimum-serving-version claim (see the resolution note on the linked deferred-work item and `spec-fix-vllm-version-checked-semantics.md`). This preset's `vllm_version_checked` was corrected back to `"0.13"` to match every other preset. The underlying fact that GLM-5.2 itself needs vLLM ≥0.23 to serve (per vLLM's own recipe page, checked at the time this preset was added) is preserved here as historical record, since the schema has no dedicated field for a model's minimum serving version.
