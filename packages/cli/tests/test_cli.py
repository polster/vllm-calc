"""Scaffold tests for the CLI (Story 1.1)."""

from typer.testing import CliRunner

from vllm_calc_cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.0.0" in result.stdout
