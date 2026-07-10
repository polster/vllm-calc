# Presets

Version-controlled model and GPU presets as YAML files — the tool's data, not code.
Adding a preset requires no engine/API change.

- `models/` — one file per model (`llama-3.3-70b.yaml`, …)
- `gpus/` — one file per GPU (`a100-80gb.yaml`, …)
- `schema/` — JSON Schema generated from the engine's Pydantic models

Each preset's `id` must match its filename stem, and every file carries provenance
(`source`, `last_verified`, `vllm_version_checked`). Files are schema-validated in CI.

**Adding a preset:** see the "Adding a model or GPU preset" section in the repo-root
[`CONTRIBUTING.md`](../CONTRIBUTING.md) — it covers the fields, how to cross-check
against the model's Hugging Face `config.json`, and the local validation command
(`uv run python -m vllm_calc_api.preset_validation`). Adding a preset is data-only: no
engine/API/SPA code change, and it appears in all surfaces after merge + a backend restart.
