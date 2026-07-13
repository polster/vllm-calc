"""Tests for pass-rate aggregation and the CI gate (Stories 4.3–4.4)."""

from vllm_calc_validation.harness import CaseResult
from vllm_calc_validation.report import summarize


def _result(label: str, *, passed: bool, fits: bool = True, under: bool = False) -> CaseResult:
    return CaseResult(
        label=label,
        fits=fits,
        predicted_bytes=100,
        measured_bytes=100,
        error_pct=0.0,
        under_prediction=under,
        passed=passed,
    )


def test_pass_rate_and_gate_when_all_pass() -> None:
    results = [_result(f"c{i}", passed=True) for i in range(10)]
    s = summarize(results, "0.13.0")
    assert s.total == 10 and s.passed == 10
    assert s.pass_rate == 1.0
    assert s.gate_passed


def test_gate_fails_below_target_pass_rate() -> None:
    results = [_result(f"c{i}", passed=i < 8) for i in range(10)]  # 80% < 90%
    s = summarize(results, "0.13.0")
    assert s.pass_rate == 0.8
    assert not s.gate_passed
    assert len(s.failures) == 2


def test_any_under_prediction_on_fits_fails_the_gate() -> None:
    # 100% pass rate on paper, but one case under-predicted a "fits" verdict.
    results = [_result(f"c{i}", passed=True) for i in range(9)]
    results.append(_result("risky", passed=False, fits=True, under=True))
    s = summarize(results, "0.13.0")
    assert s.under_predictions_on_fits == 1
    assert not s.gate_passed
