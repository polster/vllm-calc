# Presets

Version-controlled model and GPU presets as YAML files — the tool's data, not code.
Adding a preset requires no engine/API change.

- `models/` — one file per model (`llama-3.3-70b.yaml`, …)
- `gpus/` — one file per GPU (`a100-80gb.yaml`, …)
- `schema/` — JSON Schema generated from the engine's Pydantic models

The schema, loader, and curated baseline land in **Story 1.7**; CI schema validation
and provenance rules in **Story 4.1**. Each preset's `id` must match its filename stem.
