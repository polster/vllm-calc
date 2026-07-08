# Validation harness (CI-only)

Launches real `vllm serve` configurations on GPU hardware, captures actually-reserved
VRAM, and compares it to the engine's prediction — the accuracy moat, made provable.

- `runner.py` — drives vllm serve, captures reserved VRAM, diffs vs. prediction
- `matrix.yaml` — GPU × model × quant × TP cases + the pinned vLLM version
- `report.py` — computes and publishes the pass rate

Imports the engine but is **never** part of the shipped runtime image. Built in
**Epic 4** (Stories 4.3–4.4); runs on a self-hosted GPU CI runner, scheduled and on
vLLM-version bumps. Target: ≥90% within ±10%, zero under-predictions on "fits" cases.
