"""CLI tests (Stories 1.1, 3.1).

`check` is exercised end-to-end against the REAL FastAPI app in-process (via
httpx ASGITransport), so these also prove parity: the CLI's numbers come from the
same engine + endpoint the SPA uses. No network or running server required.
"""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

import vllm_calc_cli.main as cli_main
from vllm_calc_api import create_app
from vllm_calc_cli import app

runner = CliRunner()

FITS_ARGS = [
    "check", "--model", "llama-3.3-70b", "--gpu", "a100-80gb:2",
    "--tp", "2", "--ctx", "8192", "--max-seqs", "32", "--quant", "awq-4bit",
]


@pytest.fixture(autouse=True)
def _in_process_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the CLI at the real app in-process instead of a network backend."""
    application = create_app()

    def _build(_api_url: str) -> httpx.Client:
        # TestClient is a sync httpx.Client that bridges to the ASGI app in-process.
        return TestClient(application)

    monkeypatch.setattr(cli_main, "build_client", _build)


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.0.0" in result.stdout


def test_check_fits_exits_zero() -> None:
    result = runner.invoke(app, FITS_ARGS)
    assert result.exit_code == 0
    assert "Fits" in result.stdout


def test_check_no_go_exits_one_and_suggests_fixes() -> None:
    result = runner.invoke(
        app,
        ["check", "--model", "llama-3.3-70b", "--gpu", "a100-80gb:2", "--tp", "2",
         "--ctx", "131072", "--max-seqs", "32", "--quant", "awq-4bit"],
    )
    assert result.exit_code == 1
    assert "Won't fit" in result.stdout
    assert "ways to make it fit" in result.stdout


def test_check_json_emits_full_result() -> None:
    result = runner.invoke(app, [*FITS_ARGS, "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["fits"] is True
    assert payload["serve_command"].startswith("vllm serve ")
    assert "max_concurrent" in payload and "breakdown" in payload


def test_unknown_model_preset_exits_two() -> None:
    result = runner.invoke(
        app, ["check", "--model", "does-not-exist", "--gpu", "a100-80gb:2"]
    )
    assert result.exit_code == 2
    assert "Unknown model preset" in result.output
