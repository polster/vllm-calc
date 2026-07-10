"""Env-driven operational config for the self-hostable backend (Story 3.2).

CORS, rate limiting, the reported vLLM pin, and optional SPA serving are all
controlled by environment variables so one image runs hosted or air-gapped.
"""

import pytest
from fastapi.testclient import TestClient

from vllm_calc_api.main import create_app


def test_cors_origin_allowed_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://calc.example.com")
    client = TestClient(create_app())
    r = client.get("/v1/health", headers={"Origin": "https://calc.example.com"})
    assert r.headers.get("access-control-allow-origin") == "https://calc.example.com"


def test_no_cors_header_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    client = TestClient(create_app())
    r = client.get("/v1/health", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers


def test_rate_limit_returns_429_over_the_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    client = TestClient(create_app())
    assert client.get("/v1/health").status_code == 200
    assert client.get("/v1/health").status_code == 200
    blocked = client.get("/v1/health")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["type"] == "rate_limited"


def test_no_rate_limit_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    client = TestClient(create_app())
    for _ in range(5):
        assert client.get("/v1/health").status_code == 200


def test_version_range_pin_is_env_overridable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VLLM_VERSION_RANGE", ">=0.99,<1.0")
    client = TestClient(create_app())
    assert client.get("/v1/version").json()["supported_vllm_range"] == ">=0.99,<1.0"


def test_serves_bundled_spa_when_configured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    from pathlib import Path

    spa = Path(str(tmp_path)) / "spa"
    spa.mkdir()
    (spa / "index.html").write_text("<!doctype html><title>vllm-calc</title>")
    monkeypatch.setenv("SPA_DIR", str(spa))
    client = TestClient(create_app())
    # API still wins under /v1, SPA served at root.
    assert client.get("/v1/health").json()["status"] == "ok"
    root = client.get("/")
    assert root.status_code == 200
    assert "vllm-calc" in root.text
