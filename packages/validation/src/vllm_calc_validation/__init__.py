"""Accuracy validation harness for vllm-calc (dev/CI only).

Compares the engine's VRAM prediction against the VRAM a real `vllm serve` actually
reserves, so accuracy is *provable* rather than asserted. Imports the engine but is
never part of the shipped runtime image.
"""

from vllm_calc_validation.harness import (
    TOLERANCE_PCT,
    Case,
    CaseResult,
    Matrix,
    compare,
    load_matrix,
    predict,
    run_matrix,
)
from vllm_calc_validation.report import Summary, summarize

__all__ = [
    "TOLERANCE_PCT",
    "Case",
    "CaseResult",
    "Matrix",
    "compare",
    "load_matrix",
    "predict",
    "run_matrix",
    "Summary",
    "summarize",
]
