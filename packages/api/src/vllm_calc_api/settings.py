"""Runtime configuration (env-driven; no secrets in v1)."""

import os
from pathlib import Path

__all__ = ["presets_dir"]

# Repo layout: packages/api/src/vllm_calc_api/settings.py → repo root is parents[4].
_DEFAULT_PRESETS_DIR = Path(__file__).resolve().parents[4] / "presets"


def presets_dir() -> Path:
    """Directory holding `models/` and `gpus/` preset YAML (override via env)."""
    override = os.environ.get("VLLM_CALC_PRESETS_DIR")
    return Path(override) if override else _DEFAULT_PRESETS_DIR
