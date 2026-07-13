"""The validation harness: predict → measure → compare (Story 4.3).

The prediction and the pass/fail logic are pure and fully unit-tested. The single
GPU-bound step — actually launching `vllm serve` and reading reserved VRAM — is
injected as a callable so the analysis runs anywhere; the real implementation
(`measure_reserved_bytes`) requires GPU hardware + vLLM and is called on the
self-hosted GPU runner (Story 4.4).
"""

from collections.abc import Callable
from pathlib import Path

import yaml
from pydantic import BaseModel

from vllm_calc_engine.calculate import calculate
from vllm_calc_engine.models import CalcInput

__all__ = [
    "TOLERANCE_PCT",
    "Case",
    "Matrix",
    "CaseResult",
    "predict",
    "compare",
    "run_matrix",
    "load_matrix",
    "measure_reserved_bytes",
    "main",
]

# NFR1/NFR2: predictions must land within ±10% of the real reserve.
TOLERANCE_PCT = 10.0

Measure = Callable[["Case"], int]


class Case(BaseModel):
    """One matrix entry: a label plus the full engine input to size."""

    label: str
    input: CalcInput


class Matrix(BaseModel):
    """A pinned vLLM version plus the GPU × model × quant × TP cases to run."""

    vllm_version: str
    cases: list[Case]


class CaseResult(BaseModel):
    """Prediction vs. measured reserve for one case, with the pass/fail verdict."""

    label: str
    fits: bool
    predicted_bytes: int
    measured_bytes: int
    error_pct: float  # (predicted − measured) / measured × 100; positive = over-predict
    under_prediction: bool  # predicted < measured (dangerous on a "fits" verdict)
    passed: bool


def predict(case: Case) -> tuple[int, bool]:
    """Return (predicted per-GPU used bytes, fits) from the engine."""
    r = calculate(case.input)
    return r.breakdown.used_per_gpu_bytes, r.fits


def compare(label: str, predicted: int, measured: int, fits: bool) -> CaseResult:
    """Grade a single case. A pass needs ±10% accuracy AND no dangerous under-predict.

    Under-predicting on a "fits" verdict is the worst failure — we'd have told the
    user it fits when it may not — so it fails even if it lands within tolerance.
    """
    error_pct = (predicted - measured) / measured * 100 if measured else 0.0
    under_prediction = predicted < measured
    passed = abs(error_pct) <= TOLERANCE_PCT and not (fits and under_prediction)
    return CaseResult(
        label=label,
        fits=fits,
        predicted_bytes=predicted,
        measured_bytes=measured,
        error_pct=error_pct,
        under_prediction=under_prediction,
        passed=passed,
    )


def run_matrix(matrix: Matrix, measure: Measure) -> list[CaseResult]:
    """Predict, measure (via the injected callable), and compare every case."""
    results: list[CaseResult] = []
    for case in matrix.cases:
        predicted, fits = predict(case)
        measured = measure(case)
        results.append(compare(case.label, predicted, measured, fits))
    return results


def load_matrix(path: Path) -> Matrix:
    """Load and validate the case matrix from YAML."""
    return Matrix.model_validate(yaml.safe_load(path.read_text()))


def measure_reserved_bytes(case: Case) -> int:  # pragma: no cover - requires GPU + vLLM
    """Launch `vllm serve` for the case and return actually-reserved per-GPU bytes.

    Requires GPU hardware and a matching vLLM install; run on the self-hosted GPU
    runner only. Intentionally not implemented in the portable harness — inject a
    real measurement callable (or this function on a GPU host) into `run_matrix`.
    """
    raise RuntimeError(
        "measure_reserved_bytes requires GPU hardware + vLLM. Run on the GPU CI "
        "runner, or pass a measurement callable to run_matrix(). See README.md."
    )


def main() -> int:  # pragma: no cover - entry point for the GPU runner
    from vllm_calc_validation.report import summarize

    matrix = load_matrix(Path(__file__).resolve().parents[3] / "matrix.yaml")
    results = run_matrix(matrix, measure_reserved_bytes)
    summary = summarize(results, matrix.vllm_version)
    print(summary.model_dump_json(indent=2))
    return 0 if summary.gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
