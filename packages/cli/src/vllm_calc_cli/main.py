"""vllm-calc command-line entry point.

A thin client of the HTTP API: `check` resolves presets and posts a full config
to `POST /v1/calculate`, so its results are identical to the SPA's by construction
(same engine, same endpoint — parity, NFR3). Exit codes make it CI-gateable:
0 = fits, 1 = won't fit, 2 = usage/backend error.
"""

import json
import re
from typing import Any

import httpx
import typer

import vllm_calc_engine

app = typer.Typer(help="vllm-calc — will your model fit on your GPUs?", no_args_is_help=True)

DEFAULT_API_URL = "http://localhost:8000"

# Exit codes.
_EXIT_FITS = 0
_EXIT_NO_FIT = 1
_EXIT_ERROR = 2


@app.callback()
def _main() -> None:
    """vllm-calc CLI. Keeps subcommands named (e.g. `version`, `check`)."""


@app.command()
def version() -> None:
    """Print the engine version."""
    typer.echo(f"vllm-calc-engine {vllm_calc_engine.__version__}")


def build_client(api_url: str) -> httpx.Client:
    """Build the HTTP client for the backend (overridable in tests)."""
    return httpx.Client(base_url=api_url, timeout=10.0)


def _hf_ref_from_source(source: str | None) -> str | None:
    if not source:
        return None
    m = re.search(r"huggingface\.co/([^?#]+)", source)
    return m.group(1).rstrip("/") if m else None


def _find(presets: list[dict[str, Any]], preset_id: str, kind: str) -> dict[str, Any]:
    for p in presets:
        if p.get("id") == preset_id:
            return p
    ids = ", ".join(sorted(p.get("id", "?") for p in presets))
    typer.secho(f"Unknown {kind} preset '{preset_id}'. Available: {ids}", err=True, fg="red")
    raise typer.Exit(_EXIT_ERROR)


@app.command()
def check(
    model: str = typer.Option(..., "--model", help="Model preset id (e.g. llama-3.3-70b)."),
    gpu: str = typer.Option(..., "--gpu", help="GPU preset id and count, e.g. a100-80gb:2."),
    ctx: int = typer.Option(8192, "--ctx", help="Context length."),
    max_seqs: int = typer.Option(32, "--max-seqs", help="Desired concurrent sequences."),
    tp: int | None = typer.Option(None, "--tp", help="Tensor-parallel size (default: GPU count)."),
    quant: str = typer.Option("fp16", "--quant", help="Weight quantization."),
    kv_dtype: str = typer.Option("fp16", "--kv-dtype", help="KV cache dtype."),
    gpu_mem_util: float = typer.Option(0.9, "--gpu-mem-util", help="gpu_memory_utilization."),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", help="Backend base URL."),
    as_json: bool = typer.Option(False, "--json", help="Emit the full result as JSON."),
) -> None:
    """Check whether a configuration fits, gating CI (exit 1 on a no-go)."""
    gpu_id, _, count_s = gpu.partition(":")
    try:
        gpu_count = int(count_s) if count_s else 1
    except ValueError:
        typer.secho(f"Invalid --gpu '{gpu}': expected 'id:count'.", err=True, fg="red")
        raise typer.Exit(_EXIT_ERROR) from None

    # `tp or gpu_count` would swallow an explicit --tp 0; distinguish "unset" from 0.
    tp_size = gpu_count if tp is None else tp
    if tp_size < 1:
        typer.secho(f"Invalid --tp {tp}: must be ≥ 1.", err=True, fg="red")
        raise typer.Exit(_EXIT_ERROR)

    try:
        with build_client(api_url) as client:
            result = _run_check(
                client, model, gpu_id, gpu_count, tp_size, ctx, max_seqs,
                quant, kv_dtype, gpu_mem_util,
            )
    except httpx.HTTPError as exc:
        typer.secho(f"Could not reach the backend at {api_url}: {exc}", err=True, fg="red")
        raise typer.Exit(_EXIT_ERROR) from exc

    if as_json:
        typer.echo(json.dumps(result, indent=2))
    else:
        _print_human(result)

    raise typer.Exit(_EXIT_FITS if result["fits"] else _EXIT_NO_FIT)


def _run_check(
    client: httpx.Client,
    model_id: str,
    gpu_id: str,
    gpu_count: int,
    tp: int,
    ctx: int,
    max_seqs: int,
    quant: str,
    kv_dtype: str,
    gpu_mem_util: float,
) -> dict[str, Any]:
    """Resolve presets and post the configuration; returns the result object."""
    models = client.get("/v1/presets/models").raise_for_status().json()
    gpus = client.get("/v1/presets/gpus").raise_for_status().json()
    m = _find(models, model_id, "model")
    g = _find(gpus, gpu_id, "GPU")

    payload = {
        "model_ref": _hf_ref_from_source(m.get("source")),
        "total_params": m["total_params"],
        "layers": m["layers"],
        "attention_heads": m["attention_heads"],
        "kv_heads": m["kv_heads"],
        "head_dim": m["head_dim"],
        "hidden_size": m["hidden_size"],
        "attention_type": m.get("attention_type", "standard"),
        "weight_quant": quant,
        "kv_dtype": kv_dtype,
        "ctx_len": ctx,
        "max_seqs": max_seqs,
        "tensor_parallel_size": tp,
        "gpu_count": gpu_count,
        "gpu_vram_gib": g["vram_gib"],
        "gpu_memory_utilization": gpu_mem_util,
    }
    resp = client.post("/v1/calculate", json=payload)
    if resp.status_code != httpx.codes.OK:
        # A non-JSON error body (plaintext 500, proxy error page) must still exit 2,
        # not escape as an unclassified error.
        try:
            body = resp.json()
            has_error = isinstance(body, dict) and "error" in body
            msg = body["error"]["message"] if has_error else resp.text
        except ValueError:
            msg = resp.text
        typer.secho(f"Error: {msg}", err=True, fg="red")
        raise typer.Exit(_EXIT_ERROR)
    result: dict[str, Any] = resp.json()
    return result


def _print_human(r: dict[str, Any]) -> None:
    fits = r["fits"]
    typer.secho(f"{'✓' if fits else '✗'} {r['verdict']}", fg="green" if fits else "red", bold=True)
    b = r["breakdown"]
    gib = 1024**3
    typer.echo(
        f"  per-GPU: {b['used_per_gpu_bytes'] / gib:.1f} / "
        f"{b['budget_per_gpu_bytes'] / gib:.1f} GiB · "
        f"max concurrent: {r['max_concurrent']}"
    )
    for f in r.get("flags", []):
        typer.secho(f"  ⚠ {f['message']}", fg="yellow")
    for w in r.get("warnings", []):
        typer.secho(f"  ⚠ {w}", fg="yellow")
    if r.get("remediations"):
        typer.echo("  ways to make it fit: " + ", ".join(rem["label"] for rem in r["remediations"]))
    typer.echo(f"  run: {r['serve_command']}")


if __name__ == "__main__":
    app()
