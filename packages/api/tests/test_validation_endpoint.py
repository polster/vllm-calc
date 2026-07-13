"""The published-accuracy endpoint (Story 4.4)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vllm_calc_api.main import create_app


def test_pending_when_no_results_published(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("VALIDATION_RESULTS_PATH", str(tmp_path / "absent.json"))
    body = TestClient(create_app()).get("/v1/validation").json()
    assert body["status"] == "pending"
    assert body["pass_rate"] is None
    assert body["calibrated_vllm_range"]  # always reports what it's calibrated for


def test_validated_when_results_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    results = tmp_path / "validation-results.json"
    results.write_text(
        json.dumps(
            {
                "vllm_version": "0.13.0",
                "total": 12,
                "passed": 12,
                "pass_rate": 1.0,
                "under_predictions_on_fits": 0,
                "failures": [],
                "gate_passed": True,
            }
        )
    )
    monkeypatch.setenv("VALIDATION_RESULTS_PATH", str(results))
    body = TestClient(create_app()).get("/v1/validation").json()
    assert body["status"] == "validated"
    assert body["pass_rate"] == 1.0
    assert body["gate_passed"] is True
    assert body["vllm_version"] == "0.13.0"
