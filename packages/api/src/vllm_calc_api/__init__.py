"""FastAPI backend for vllm-calc.

Thin HTTP layer over the engine. Owns no calculation logic (parity invariant).
Story 1.1 scaffolds the app with meta endpoints; /v1/calculate and preset
endpoints arrive in Stories 1.7–1.8.
"""

__all__ = ["create_app"]

from vllm_calc_api.main import create_app
