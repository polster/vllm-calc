"""Smoke tests for the engine scaffold (Story 1.1).

These lock the package's importability and the units invariant. Real
calculation tests (golden values) arrive with Stories 1.2–1.6.
"""

import vllm_calc_engine


def test_package_imports_and_reports_version() -> None:
    assert vllm_calc_engine.__version__ == "0.0.0"


def test_units_invariant_gib_is_binary() -> None:
    # The engine computes in bytes; GiB is a binary (1024^3) edge conversion.
    assert vllm_calc_engine.GIB == 1073741824
