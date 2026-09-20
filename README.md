# vllm-calc

A VRAM calculator for serving open-source LLMs with vLLM. Pick a GPU, a model, a
quantization, a context length, and a tensor-parallel size — and find out, before
you launch anything, whether it fits, how many concurrent requests it serves, and
the exact `vllm serve` command to run it.

## Repository layout

```
packages/
  engine/   # pure, I/O-free calculation core (the single source of truth)
  api/      # FastAPI app exposing the engine over /v1
  cli/      # Typer CLI (thin client of the API)
web/        # React + Vite + TypeScript SPA
presets/    # version-controlled model & GPU presets (YAML)
validation/ # CI-only accuracy harness (drives real vllm serve)
docker/     # backend image + local run
```

## Development

See [CONTRIBUTION.md]() for more details.

### Quality gates (what CI runs)

```bash
# Python
uv run ruff check .
uv run mypy .
uv run pytest

# Web
cd web && npm run lint && npm run typecheck && npm test && npm run build
```

See [docs/](docs/) for the full planning chain (PRD, architecture, UX, epics).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
