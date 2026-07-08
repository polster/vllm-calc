"""Typer CLI for vllm-calc.

A thin client of the API (and engine). Story 1.1 scaffolds the app with a
`version` command; the `check` command (CI-gating, --json, non-zero exit on
no-go) arrives in Story 3.1.
"""

__all__ = ["app"]

from vllm_calc_cli.main import app
