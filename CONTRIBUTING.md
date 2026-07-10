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

## Adding a model or GPU preset (no code change)

Presets are **data**: add a YAML file under `presets/models/` or `presets/gpus/` and
open a PR. No engine/API/SPA code changes — the backend loads and validates every
preset at startup, so a merged preset appears in the API, SPA, and CLI after a restart.

### 1. Create the file

- Filename **is** the id: `presets/models/qwen2.5-32b.yaml` → `id: qwen2.5-32b`.
- Match the JSON Schema in `presets/schema/` (generated from the engine's Pydantic
  models — the source of truth). Fields:

**Model** (`presets/models/<id>.yaml`):

```yaml
id: qwen2.5-32b                 # must equal the filename stem
name: Qwen2.5 32B
total_params: 32500000000       # TOTAL params. For MoE: ALL experts, not active.
layers: 64
attention_heads: 40
kv_heads: 8                      # GQA: the real KV-head count (not attention_heads)
head_dim: 128
hidden_size: 5120
is_moe: false
attention_type: standard        # standard | mla | sliding_window | other
source: https://huggingface.co/Qwen/Qwen2.5-32B      # provenance
last_verified: "2026-07-10"
vllm_version_checked: "0.13"
```

**GPU** (`presets/gpus/<id>.yaml`):

```yaml
id: rtx-6000-ada
name: NVIDIA RTX 6000 Ada
vram_gib: 48
source: https://www.nvidia.com/.../rtx-6000-ada/
last_verified: "2026-07-10"
vllm_version_checked: "0.13"
```

### 2. Cross-check against the model's `config.json`

Get the architecture numbers from the model's published `config.json` on Hugging Face
(don't guess):

| preset field | `config.json` key |
|---|---|
| `layers` | `num_hidden_layers` |
| `attention_heads` | `num_attention_heads` |
| `kv_heads` | `num_key_value_heads` (GQA; equals `num_attention_heads` for MHA) |
| `hidden_size` | `hidden_size` |
| `head_dim` | `head_dim` if present, else `hidden_size / num_attention_heads` |
| `attention_type` | `mla` for DeepSeek-style MLA, `sliding_window` if a window is set, else `standard` |

For MoE, `total_params` is **all experts combined** (the on-disk weight count), not the
active-per-token count — the calculator sizes stored weights. Set `is_moe: true`.

If a model's architecture is genuinely unusual and you can't map it cleanly, set
`attention_type: other` so the result is honestly flagged rather than silently wrong.

### 3. Validate before pushing

```bash
uv run python -m vllm_calc_api.preset_validation
```

This is exactly what CI runs. It fails on any schema/provenance/id-mismatch violation
and warns if a `is_moe` preset's `total_params` looks like an active-only count.
Regenerate the committed schemas after an engine model change with
`write_schemas` (see `preset_validation.py`).
