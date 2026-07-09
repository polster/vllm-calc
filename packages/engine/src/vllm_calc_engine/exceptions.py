"""Typed domain exceptions raised by the engine.

The engine raises these for genuine invalid input / constraint violations; the
API layer translates them into the structured error contract. (Calculable-but-
limited results — e.g. MLA over-provision — are carried as result *flags*, never
raised; see Story 2.4.)
"""

__all__ = ["EngineError", "InvalidParallelism", "UnsupportedArchitecture"]


class EngineError(Exception):
    """Base class for all engine domain errors."""


class InvalidParallelism(EngineError):
    """A tensor-parallel configuration is invalid (divisibility / GPU-count)."""


class UnsupportedArchitecture(EngineError):
    """The model architecture is not supported by the calculation."""
