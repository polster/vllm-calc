---
title: 'Fix vllm_version_checked field semantics'
type: 'bugfix'
created: '2026-09-07'
status: 'done'
route: 'one-shot'
---

# Fix vllm_version_checked field semantics

## Intent

**Problem:** A deferred-work item claimed the engine's `SUPPORTED_VLLM_RANGE` (`0.13`–`<0.14`) was "stale" relative to `glm-5.2.yaml`'s `vllm_version_checked: "0.23"`. Investigating it revealed the real bug was the opposite: `vllm_version_checked` is per-preset provenance for the project's own baseline vLLM version (matching `SUPPORTED_VLLM_RANGE`, per NFR16) at time of verification — not a claim about a specific model's minimum serving requirement. Every other of the 43 existing presets uses `"0.13"`; only `glm-5.2.yaml` had been set to `"0.23"`, using the wrong semantic (vLLM's own minimum version to serve GLM-5.2's `glm_moe_dsa` architecture).

**Approach:** Correct `glm-5.2.yaml`'s `vllm_version_checked` back to `"0.13"`. Clarify the field's true meaning in `models.py`'s `Field(description=...)` and in `CONTRIBUTING.md` so future contributors don't repeat the mistake. Correct the deferred-work.md entry and the original GLM-5.2 spec in place (append-only annotations, not rewrites) rather than silently deleting the historical record of the (wrong) original claim. `SUPPORTED_VLLM_RANGE` itself is untouched — it's an empirically-calibrated, app-wide claim (NFR16) that only the Epic 4 GPU validation harness can responsibly change; no GPU recalibration was needed or attempted here.

## Suggested Review Order

- The actual semantic fix: `vllm_version_checked` corrected to match every other preset, field description clarified for future contributors.
  [`glm-5.2.yaml`](../presets/models/glm-5.2.yaml) · [`models.py`](../packages/engine/src/vllm_calc_engine/models.py) · [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- Correction of the two docs that had recorded/relied on the wrong premise, done as append-only annotations rather than erasing the original (wrong) claims, so the historical record of what was believed at each point stays legible.
  [`deferred-work.md`](../docs/deferred-work.md#engines-supported_vllm_range-is-stale-relative-to-newer-presets-vllm_version_checked) · [`spec-add-glm-5.2-preset.md`](../docs/spec-add-glm-5.2-preset.md)
