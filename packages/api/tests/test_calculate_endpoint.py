"""Tests for the /v1/calculate and preset endpoints + error contract (Story 1.8)."""

from fastapi.testclient import TestClient

from vllm_calc_api import create_app

client = TestClient(create_app())

FITS_BODY = {
    "total_params": 70_000_000_000,
    "layers": 80,
    "attention_heads": 64,
    "kv_heads": 8,
    "head_dim": 128,
    "hidden_size": 8192,
    "weight_quant": "awq-4bit",
    "kv_dtype": "fp16",
    "ctx_len": 8192,
    "max_seqs": 32,
    "tensor_parallel_size": 2,
    "gpu_count": 2,
    "gpu_vram_gib": 80,
}


def test_calculate_returns_full_result_snake_case() -> None:
    resp = client.post("/v1/calculate", json=FITS_BODY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["fits"] is True
    assert body["max_concurrent"] == 42
    assert "verdict" in body and "supported_vllm_range" in body
    # snake_case on the wire, nested breakdown present
    assert body["breakdown"]["weights_per_gpu_bytes"] == 17_500_000_000
    assert "available_for_kv_bytes" in body["breakdown"]


def test_calculate_constraint_violation_maps_to_400() -> None:
    bad_tp = {**FITS_BODY, "tensor_parallel_size": 3, "gpu_count": 3}
    resp = client.post("/v1/calculate", json=bad_tp)
    assert resp.status_code == 400
    err = resp.json()["error"]
    assert err["type"] == "constraint_violation"
    assert "attention" in err["message"].lower() or "tensor" in err["message"].lower()


def test_calculate_request_validation_maps_to_422() -> None:
    incomplete = {k: v for k, v in FITS_BODY.items() if k != "total_params"}
    resp = client.post("/v1/calculate", json=incomplete)
    assert resp.status_code == 422
    assert resp.json()["error"]["type"] == "validation"


def test_list_model_presets() -> None:
    resp = client.get("/v1/presets/models")
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.json()}
    assert "llama-3.3-70b" in ids and "mixtral-8x7b" in ids


def test_list_gpu_presets() -> None:
    resp = client.get("/v1/presets/gpus")
    assert resp.status_code == 200
    gpus = {g["id"]: g for g in resp.json()}
    assert gpus["a100-80gb"]["vram_gib"] == 80


def test_openapi_exposes_calculate() -> None:
    schema = client.get("/openapi.json").json()
    assert "/v1/calculate" in schema["paths"]
