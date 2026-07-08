"""vllm-calc calculation engine.

Pure, deterministic, I/O-free. This package is the single source of truth for the
VRAM calculation and owns the shared Pydantic I/O models imported by the API and
CLI. Calculation logic lives here and nowhere else (parity invariant, NFR3).

Story 1.1 scaffolds the package; the model (weights, KV cache, overhead, TP
sharding, capacity, remediation, command) is implemented in Stories 1.2–1.6 / 2.x.
"""

__all__ = ["__version__", "GIB"]

__version__ = "0.0.0"

# Project-critical units rule: the engine computes in integer BYTES only.
# Conversion to GiB happens at presentation edges, never inside the math.
GIB = 1024**3
