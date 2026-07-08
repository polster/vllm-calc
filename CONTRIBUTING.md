# Contributing to vllm-calc

## Golden rules (non-negotiable)

These encode the architecture's consistency rules. AI agents and humans both follow them.

1. **Compute in bytes.** The engine computes VRAM in **integer bytes only**. Convert to
   GiB (1024³) at presentation edges (SPA/CLI), never inside the math. No GB/GiB
   arithmetic in `packages/engine`.
2. **One engine, one source of truth.** All calculation logic lives in
   `packages/engine`. The API and CLI **import** it; the SPA calls the API. **Never**
   re-implement the calculation in TypeScript — that breaks the parity invariant (NFR3).
3. **Shared models are engine-owned.** Pydantic I/O models live in the engine and are
   imported by API and CLI. Do not redefine them elsewhere.
4. **snake_case on the wire.** API JSON uses snake_case field names (matches Python);
   the SPA maps to camelCase at its own boundary.
5. **Return results-with-flags, don't throw, for over-provision.** A calculable-but-
   limited answer (MLA / sliding-window) returns a value **plus** a flag. Only genuine
   invalid input / constraint violations raise typed engine exceptions.
6. **Presets are data.** Add a model/GPU by adding a YAML file under `presets/` — no
   code change. Files are schema-validated in CI and carry provenance.

## Toolchain

Python uses **uv** (workspace + `uv.lock`), as the architecture intended — `packages/*`
form a uv workspace and the API/CLI resolve the engine via
`[tool.uv.sources] vllm-calc-engine = { workspace = true }`. The web side uses **npm**
(a documented divergence from the architecture's pnpm suggestion — same standard tooling,
different runner). Reproducibility comes from the committed `uv.lock` and `web/package-lock.json`.

## Local development

```bash
# Python — one command sets up the whole workspace from the lockfile
uv sync

# Web
cd web && npm install
```

## Before you push (what CI enforces)

```bash
uv run ruff check . && uv run mypy . && uv run pytest        # Python
cd web && npm run lint && npm run typecheck && npm test && npm run build   # Web
```

New engine behavior ships with **golden-value tests**. New surfaces must produce
**identical** results to the engine for identical inputs.
