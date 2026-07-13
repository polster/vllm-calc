"""Published accuracy status endpoint (Story 4.4).

Surfaces the last GPU-validation pass rate to users at the point of use. Until the
self-hosted GPU runner publishes a results file, the status is honestly "pending"
rather than a made-up number.
"""

import json

from fastapi import APIRouter
from pydantic import BaseModel

from vllm_calc_api import settings

router = APIRouter(tags=["meta"])


class ValidationStatus(BaseModel):
    status: str  # "validated" | "pending"
    calibrated_vllm_range: str
    vllm_version: str | None = None
    pass_rate: float | None = None
    passed: int | None = None
    total: int | None = None
    gate_passed: bool | None = None


@router.get("/validation")
def validation() -> ValidationStatus:
    calibrated = settings.vllm_version_range()
    path = settings.validation_results_path()
    if not path.is_file():
        return ValidationStatus(status="pending", calibrated_vllm_range=calibrated)
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        # A truncated/half-written results file (the harness write isn't atomic) must
        # not 500 — report "pending" until a valid summary is published.
        return ValidationStatus(status="pending", calibrated_vllm_range=calibrated)
    return ValidationStatus(
        status="validated",
        calibrated_vllm_range=calibrated,
        vllm_version=data.get("vllm_version"),
        pass_rate=data.get("pass_rate"),
        passed=data.get("passed"),
        total=data.get("total"),
        gate_passed=data.get("gate_passed"),
    )
