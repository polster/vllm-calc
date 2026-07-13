"""Aggregate case results into a publishable, gate-able summary (Stories 4.3–4.4)."""

from pydantic import BaseModel

from vllm_calc_validation.harness import CaseResult

__all__ = ["PASS_RATE_TARGET", "Summary", "summarize"]

# NFR2: at least 90% of cases within ±10%, with zero under-predictions on "fits".
PASS_RATE_TARGET = 0.90


class Summary(BaseModel):
    """Publishable accuracy summary for a validation run against a pinned vLLM."""

    vllm_version: str
    total: int
    passed: int
    pass_rate: float  # 0..1
    under_predictions_on_fits: int
    failures: list[str]  # labels of cases that did not pass
    gate_passed: bool  # pass_rate ≥ target AND zero under-predictions on "fits"


def summarize(results: list[CaseResult], vllm_version: str) -> Summary:
    """Compute the pass rate and the CI gate verdict from per-case results."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    under = sum(1 for r in results if r.fits and r.under_prediction)
    rate = passed / total if total else 0.0
    return Summary(
        vllm_version=vllm_version,
        total=total,
        passed=passed,
        pass_rate=rate,
        under_predictions_on_fits=under,
        failures=[r.label for r in results if not r.passed],
        gate_passed=rate >= PASS_RATE_TARGET and under == 0,
    )
