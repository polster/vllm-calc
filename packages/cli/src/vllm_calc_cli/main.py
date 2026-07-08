"""vllm-calc command-line entry point."""

import typer

import vllm_calc_engine

app = typer.Typer(help="vllm-calc — will your model fit on your GPUs?", no_args_is_help=True)


@app.callback()
def _main() -> None:
    """vllm-calc CLI. Keeps subcommands named (e.g. `version`, and `check` from Story 3.1)."""


@app.command()
def version() -> None:
    """Print the engine version."""
    typer.echo(f"vllm-calc-engine {vllm_calc_engine.__version__}")


if __name__ == "__main__":
    app()
