"""Build honesty flags for a result (Story 2.4).

Flags are carried in the result, never raised — the user always gets a labeled
number instead of a silently-wrong one. Flag `type` values align with the API
error contract's non-fatal kinds: `over_provision_estimate`, `unsupported`.
"""

from vllm_calc_engine.attention import AttentionType
from vllm_calc_engine.models import CalcInput, Flag

__all__ = ["build_flags"]

_OVER_PROVISION = {
    AttentionType.MLA: (
        "This model uses MLA (multi-head latent attention). The generic KV-cache "
        "formula over-provisions here, so the real footprint is likely smaller — "
        "treat this as a conservative upper bound."
    ),
    AttentionType.SLIDING_WINDOW: (
        "This model uses sliding-window attention. The generic KV-cache formula "
        "assumes full context per sequence and over-provisions — treat this as a "
        "conservative upper bound."
    ),
}


def build_flags(inp: CalcInput) -> list[Flag]:
    """Return honesty flags for the configuration (empty for standard attention)."""
    if inp.attention_type in _OVER_PROVISION:
        return [Flag(type="over_provision_estimate", message=_OVER_PROVISION[inp.attention_type])]
    if inp.attention_type == AttentionType.OTHER:
        return [
            Flag(
                type="unsupported",
                message=(
                    "This architecture isn't specifically calibrated in v1. The estimate "
                    "uses the generic formula and may be inaccurate — verify before relying on it."
                ),
            )
        ]
    return []
