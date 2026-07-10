"""Runtime configuration (env-driven; no secrets in v1).

All operational knobs are environment variables so the same image runs hosted or
air-gapped with no code change (NFR8): presets dir, CORS origins, rate-limit
toggle, reported vLLM version pin, and an optional bundled-SPA directory.
"""

import os
from pathlib import Path

from vllm_calc_engine.constants import SUPPORTED_VLLM_RANGE

__all__ = [
    "presets_dir",
    "cors_origins",
    "rate_limit_enabled",
    "rate_limit_per_minute",
    "vllm_version_range",
    "spa_dir",
]

# Repo layout: packages/api/src/vllm_calc_api/settings.py → repo root is parents[4].
_DEFAULT_PRESETS_DIR = Path(__file__).resolve().parents[4] / "presets"

_TRUTHY = {"1", "true", "yes", "on"}


def presets_dir() -> Path:
    """Directory holding `models/` and `gpus/` preset YAML (override via env)."""
    override = os.environ.get("VLLM_CALC_PRESETS_DIR")
    return Path(override) if override else _DEFAULT_PRESETS_DIR


def cors_origins() -> list[str]:
    """Allowed CORS origins (comma-separated `CORS_ORIGINS`; empty = same-origin)."""
    raw = os.environ.get("CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def rate_limit_enabled() -> bool:
    """Whether the fixed-window rate limiter is active (`RATE_LIMIT_ENABLED`)."""
    return os.environ.get("RATE_LIMIT_ENABLED", "").strip().lower() in _TRUTHY


def rate_limit_per_minute() -> int:
    """Requests/minute/client allowed when rate limiting is on (`RATE_LIMIT_PER_MINUTE`)."""
    try:
        return int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))
    except ValueError:
        return 120


def vllm_version_range() -> str:
    """The reported calibrated vLLM range (`VLLM_VERSION_RANGE` overrides the engine's)."""
    return os.environ.get("VLLM_VERSION_RANGE") or SUPPORTED_VLLM_RANGE


def spa_dir() -> Path | None:
    """Optional directory of built static SPA assets to serve (`SPA_DIR`)."""
    raw = os.environ.get("SPA_DIR")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None
