"""Tests for the portable (non-GPU) parts of the harness (Story 4.3)."""

from pathlib import Path

import pytest
from vllm_calc_validation.harness import (
    Matrix,
    compare,
    load_matrix,
    measure_reserved_bytes,
    predict,
    run_matrix,
)

MATRIX_PATH = Path(__file__).resolve().parents[1] / "matrix.yaml"


def test_compare_over_prediction_within_tolerance_passes() -> None:
    # Predicted 5% above measured on a fits case → conservative and within ±10%.
    r = compare("case", predicted=105, measured=100, fits=True)
    assert r.error_pct == pytest.approx(5.0)
    assert not r.under_prediction
    assert r.passed


def test_compare_under_prediction_on_fits_fails_even_within_tolerance() -> None:
    # Only 2% low, but under-predicting a "fits" verdict is unsafe → fail.
    r = compare("case", predicted=98, measured=100, fits=True)
    assert r.under_prediction
    assert not r.passed


def test_compare_under_prediction_on_no_fit_can_still_pass() -> None:
    # A no-go case that under-predicts within tolerance is not a safety failure.
    r = compare("case", predicted=98, measured=100, fits=False)
    assert r.passed


def test_compare_out_of_tolerance_fails() -> None:
    r = compare("case", predicted=130, measured=100, fits=True)
    assert not r.passed


def test_compare_non_positive_measurement_fails_loudly() -> None:
    # A broken measurement (0 bytes) must fail, not grade as a perfect 0% error.
    r = compare("case", predicted=100, measured=0, fits=True)
    assert not r.passed
    assert not r.under_prediction


def test_run_matrix_uses_injected_measurement() -> None:
    matrix = load_matrix(MATRIX_PATH)
    # Fake "measured" = 3% BELOW prediction → every case conservatively over-predicts
    # (predicted > measured) and lands within ±10%, so all pass.
    results = run_matrix(matrix, lambda case: int(predict(case)[0] * 0.97))
    assert len(results) == len(matrix.cases)
    assert all(r.passed for r in results)


def test_load_matrix_and_predict_run_without_gpu() -> None:
    matrix = load_matrix(MATRIX_PATH)
    assert matrix.vllm_version
    assert len(matrix.cases) >= 1
    predicted, fits = predict(matrix.cases[0])
    assert predicted > 0 and isinstance(fits, bool)


def test_real_measurement_requires_gpu() -> None:
    case = Matrix.model_validate(
        {"vllm_version": "0.13.0", "cases": load_matrix(MATRIX_PATH).cases}
    ).cases[0]
    with pytest.raises(RuntimeError, match="GPU"):
        measure_reserved_bytes(case)
