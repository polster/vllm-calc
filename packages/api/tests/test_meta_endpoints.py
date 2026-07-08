"""Scaffold tests for the API meta endpoints (Story 1.1)."""

from fastapi.testclient import TestClient

from vllm_calc_api import create_app

client = TestClient(create_app())


def test_health_ok() -> None:
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_version_reports_engine_and_vllm_range() -> None:
    resp = client.get("/v1/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine_version"] == "0.0.0"
    assert body["supported_vllm_range"].startswith(">=0.13")
