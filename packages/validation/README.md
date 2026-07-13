# Validation harness (dev/CI only)

Launches real `vllm serve` configurations on GPU hardware, captures actually-reserved
VRAM, and compares it to the engine's prediction — the accuracy moat, made provable.
A dev-only workspace package; **never shipped in the runtime Docker image**.

- `src/vllm_calc_validation/harness.py` — `predict` (engine) → `measure` (real `vllm serve`)
  → `compare`; pure prediction + pass/fail logic (unit-tested), GPU measurement injected.
- `src/vllm_calc_validation/report.py` — `summarize` → pass rate + CI gate verdict.
- `matrix.yaml` — GPU × model × quant × TP cases + the pinned vLLM version.

## Pass criteria (NFR2)

A case passes when the prediction is within **±10%** of the real reserve **and** does
not under-predict a "fits" verdict (that would tell a user it fits when it may not).
The gate passes when **≥90%** of cases pass **and** there are **zero** under-predictions
on "fits" cases.

## Running

The portable analysis (prediction, comparison, aggregation) runs anywhere and is
covered by `pytest`. The full run needs a GPU host with a matching vLLM:

```sh
vllm-calc-validate           # runs matrix.yaml, prints the JSON summary, exits non-zero if the gate fails
```

`measure_reserved_bytes` is intentionally GPU-only; on non-GPU hosts, inject a
measurement callable into `run_matrix()` (this is how the tests exercise it).
Runs on the self-hosted GPU runner (`.github/workflows/validation-gpu.yml`),
scheduled and on vLLM-version bumps (Story 4.4).
