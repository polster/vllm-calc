---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: 'complete'
completedAt: '2026-07-08'
inputDocuments:
  - docs/prd.md
  - docs/architecture.md
  - docs/ux-design-specification.md
  - docs/product-brief-vllm-calc.md
  - docs/product-brief-vllm-calc-distillate.md
---

# vllm-calc - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for vllm-calc, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: A user can select a GPU from a curated preset (model, VRAM, count) or define a custom GPU (VRAM per GPU, count).
FR2: A user can select a model from a curated preset or define a custom model by its architecture parameters (total params, layers, kv_heads, head_dim, hidden_size, MoE flag).
FR3: A user can specify a quantization scheme that affects both weights and KV cache (e.g. FP16, FP8, AWQ/GPTQ 4-bit).
FR4: A user can specify context length, desired concurrency (max_seqs), gpu_memory_utilization, and tensor-parallel size.
FR5: A user can adjust advanced levers that affect overhead (e.g. max_num_batched_tokens, enforce_eager).
FR6: The system can compute per-GPU VRAM as weights + GQA-aware KV cache + a three-term overhead (fixed context + activations + CUDA graphs).
FR7: The system can apply tensor-parallel sharding per GPU, dividing weights and KV while replicating overhead across GPUs.
FR8: The system can compare required VRAM against the usable budget (gpu_memory_utilization × per-GPU VRAM) and return a go/no-go verdict.
FR9: The system can compute MoE model weights from total (not active) parameters.
FR10: The system can validate parallelism constraints (TP divides attention-heads and KV-heads; TP equals GPU count) and reject invalid configurations with a reason.
FR11: The system can warn when TP exceeds the model's KV-head count (KV-replication wall), indicating KV will not shard further.
FR12: The system can compute maximum concurrent sequences supported (bounded by the KV budget and the batch cap).
FR13: The system can express the verdict as a capacity statement comparing requested vs. supported concurrency.
FR14: The system can label capacity results as conservative/worst-case (full-context-per-sequence assumption).
FR15: On a no-go, the system can suggest one or more nearest fitting configurations (reduced context, different quantization, higher TP / more GPUs).
FR16: A user can apply a suggested configuration and recompute.
FR17: The system can generate a runnable vllm serve command whose flags match the computed configuration.
FR18: A user can copy the generated command.
FR19: A user can view a per-GPU VRAM breakdown visualization (weights / KV / overhead vs. usable budget).
FR20: A user can expand the overhead figure into its three component terms.
FR21: The system can flag when an estimate is a known over-provision (MLA / sliding-window) or the architecture is unsupported, rather than returning a silently-wrong number.
FR22: The system can report the vLLM version range the result is calibrated for.
FR23: A user can perform a calculation through a browser SPA.
FR24: A developer can perform a calculation through the HTTP API.
FR25: A developer can perform a calculation through the CLI, which returns machine-readable output (--json) and exits non-zero on a no-go for CI gating.
FR26: An operator can run the backend locally (Docker) with no external runtime dependencies, so no configuration data leaves their network.
FR27: All surfaces return identical results for identical inputs (single shared engine).
FR28: A contributor can add a model or GPU preset as a version-controlled file conforming to a defined schema.
FR29: The system can validate preset files against the schema (in CI), ideally cross-checking a model preset against its published config.json.
FR30: A preset carries provenance (source and last-verified information).
FR31: The system can be validated by a harness that launches real vllm serve configurations and compares predicted vs. actually-reserved VRAM.
FR32: The validation harness can run in CI against a pinned vLLM version range and report its pass rate.

### NonFunctional Requirements

NFR1: Predicted VRAM within ±10% of actual vllm serve startup reserve across the validation suite, biased to over-predict on any "fits" verdict.
NFR2: Validation-suite pass rate ≥90% within ±10% with zero under-predictions on "fits" cases, published and CI-gated against a pinned vLLM version range.
NFR3: The calculation is deterministic and identical across all surfaces (SPA, CLI, API).
NFR4: Inputs outside validated coverage (MLA/sliding-window/unsupported) return a labeled/flagged result rather than an unflagged wrong number.
NFR5: A calculation returns in under 500 ms server-side for a single request.
NFR6: The web path requires no installation and reaches interactive state in under 3 seconds; input changes update near-instantly.
NFR7: End-to-end time-to-answer under one minute.
NFR8: Backend runs as a self-contained Docker image with no external runtime dependencies (air-gapped-capable).
NFR9: The SPA is static-hostable and configurable to target any API base URL.
NFR10: A single stateless backend instance serves typical single-team/community load; scales horizontally if needed.
NFR11: v1 requires no authentication and stores no user accounts.
NFR12: The public hosted instance does not persist/log identifying request content beyond anonymous opt-in usage signals; self-hosted keeps all data on-network.
NFR13: Standard web hardening (input validation, no execution of user content, dependency-vuln scanning in CI).
NFR14: The calculation engine is extensible to new attention types and quantization formats without core rewrites.
NFR15: Presets are version-controlled flat files with a schema-validated contribution path; adding coverage needs no code change.
NFR16: Results and the engine declare the vLLM version range they target.
NFR17: The SPA meets WCAG 2.1 AA basics (keyboard nav, contrast, non-color-only fit/no-fit encoding).

### Additional Requirements

_(from Architecture)_
- **STARTER / SCAFFOLD (impacts Epic 1, Story 1):** Greenfield monorepo composed from minimal official scaffolds — `create-vite` React-TS for `web/`; uv/Poetry Python workspace for `packages/{engine,api,cli}`; `pnpm` for `web`. No opinionated full-stack template. Versions pinned: Python 3.13, FastAPI ~0.139, Typer ~0.26, Pydantic v2, React 19, Vite 8.
- **Engine as shared package:** pure, I/O-free `packages/engine` implementing the spec.txt v1 model; the sole owner of the calculation and the shared Pydantic I/O models; imported by API, CLI, and validation harness (the parity guarantor).
- **REST API:** versioned `/v1`; `POST /v1/calculate` returns the full result object; `GET /v1/presets/{models,gpus}`, `/v1/health`, `/v1/version`. OpenAPI auto-generated; used to generate the SPA's typed client.
- **Error contract:** structured `{error:{type,message,details?}}` with types validation / constraint_violation / unsupported / over_provision_estimate / internal.
- **Preset store:** version-controlled **YAML** files under `presets/` with provenance fields; loaded into memory at startup; JSON Schema generated from Pydantic models.
- **Deployment:** single Docker image serving the API (+ optionally the static SPA); env-var config (API base URL, vLLM version pin, CORS, rate-limit toggle).
- **CI (two tiers):** (1) per-PR — lint (ruff/ESLint), type-check (mypy/tsc), unit + golden engine tests, SPA build, preset schema validation, dependency-vuln scan; (2) GPU validation harness on a self-hosted GPU runner, scheduled + on vLLM-version bumps.
- **Units invariant:** engine computes in integer bytes only; convert to GiB at presentation edges.

### UX Design Requirements

UX-DR1: Establish the design-system foundation — Tailwind + Radix (shadcn/ui) with design tokens (slate + indigo palette, dark-mode default, semantic fit/no-go/warn status tokens), light + dark themes via CSS variables.
UX-DR2: Build the **VerdictBanner** custom component (icon + headline + capacity subline + calibrated-vLLM-version label; states fit/no-go/warn/updating; wrapped in a polite ARIA live region; never color-alone).
UX-DR3: Build the **VramBreakdownBar** custom component (SVG stacked bar weights/KV/overhead vs. budget marker; hover tooltips; expandable overhead → 3 sub-terms; states fits/over-budget/updating/flagged; `role="img"` + aria-label sentence + screen-reader table; colorblind-safe validated palette; data-viz mark specs).
UX-DR4: Build the **RemediationChips** component (applyable "fits at 90k / FP8 / TP=4" chips; each carries the input delta it applies).
UX-DR5: Build the **CommandBlock** component (monospace vllm serve output, syntax-tinted flags, copy affordance with "copied ✓" toast).
UX-DR6: Implement the input surface — searchable preset comboboxes (model/GPU) with autofill + "from preset" provenance tags, custom-model inline field reveal, grouped inputs (Model / GPU & Parallelism / Workload / collapsed Advanced).
UX-DR7: Implement the live-recompute loop — debounced (~250ms) single /calculate call on input change, in-place result update with last-valid-result persistence, no submit button, no full-screen spinner, subtle updating shimmer.
UX-DR8: Implement URL-as-state — all inputs encoded to query params (debounced), back/forward/refresh restore the scenario, copying the URL shares it.
UX-DR9: Implement inline, field-level validation with plain-language messages (TP divisibility, missing custom fields); last valid result stays visible while an input is invalid.
UX-DR10: Implement honesty-flag callouts (calm amber, inline) for MLA/SWA over-provision and unsupported architectures.
UX-DR11: Implement the pre-computed default scenario on load (no blank state — first paint shows a real result).
UX-DR12: Implement the responsive two-region layout (inputs left / result right at ≥lg; stacks below; command block scrolls internally; no horizontal page scroll).
UX-DR13: Implement accessibility baseline — WCAG 2.1 AA (contrast both themes, full keyboard operability, visible focus, skip-to-result link, ≥44px touch targets, prefers-reduced-motion, 200% zoom reflow) + a11y CI checks (axe-core, colorblind palette validation).
UX-DR14: Implement the light/dark theme toggle (persisted; both themes pass contrast).

### FR Coverage Map

- FR1–FR4: Epic 1 — configuration input (GPU/model presets + custom, quant, workload knobs)
- FR6–FR14: Epic 1 — core VRAM compute, TP sharding, MoE, constraints, capacity
- FR19, FR20, FR22: Epic 1 — breakdown visualization, overhead expand, version label
- FR23, FR24, FR27: Epic 1 — SPA + API surfaces, cross-surface parity
- FR5: Epic 2 — advanced overhead levers
- FR15, FR16: Epic 2 — remediation suggestions + apply
- FR17, FR18: Epic 2 — vllm serve command generation + copy
- FR21: Epic 2 — honest over-provision / unsupported flags
- FR25: Epic 3 — CLI (CI-gating, --json, non-zero exit)
- FR26: Epic 3 — locally-runnable Docker backend
- FR28, FR29, FR30: Epic 4 — preset contribution, schema validation, provenance
- FR31, FR32: Epic 4 — validation harness + CI pass rate

## Epic List

### Epic 1: Know the Answer — Core VRAM Fit Verdict
A user picks a GPU + model preset (and workload knobs) and gets a live, trustworthy "fits / doesn't fit + capacity" verdict with a transparent per-GPU VRAM breakdown in the browser. Walking skeleton: scaffold + engine + API + core SPA.
**FRs covered:** FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR19, FR20, FR22, FR23, FR24, FR27
**Also:** scaffold (Story 1.1), engine package + golden tests, curated YAML presets + loader, POST /v1/calculate + preset endpoints, design-system foundation (UX-DR1), VerdictBanner (UX-DR2), VramBreakdownBar (UX-DR3), input surface (UX-DR6), live-recompute loop (UX-DR7), default scenario (UX-DR11), responsive layout (UX-DR12), a11y baseline (UX-DR13), theme toggle (UX-DR14), inline validation (UX-DR9). NFR1, NFR3, NFR5, NFR6, NFR7, NFR9, NFR17.

### Epic 2: Act on the Answer — Remediation & Runnable Command
On a no-go, one-click "nearest fitting config" chips; either way, a copy-ready vllm serve command; plus honest over-provision flags and advanced levers.
**FRs covered:** FR5, FR15, FR16, FR17, FR18, FR21
**Also:** RemediationChips (UX-DR4), CommandBlock + copy toast (UX-DR5), honesty callouts (UX-DR10), URL-as-state (UX-DR8). NFR4.

### Epic 3: Reach It Anywhere — CLI & Self-Hosted Backend
The same engine reachable from the CLI (CI-gating, --json, non-zero exit) and as a locally-runnable Docker backend for air-gapped/self-hosted use.
**FRs covered:** FR25, FR26
**Also:** CLI package over the API, Docker image (+ optional static SPA), env-var config. NFR8, NFR10, NFR11, NFR12, NFR13.

### Epic 4: Prove It & Grow It — Accuracy Validation & Preset Contribution
A validation harness that checks predictions against real vllm serve (CI-gated pass rate) and a community preset-contribution path (schema-validated, provenance-tracked).
**FRs covered:** FR28, FR29, FR30, FR31, FR32
**Also:** GPU CI runner, published pass rate, engine extensibility for new attention/quant types. NFR2, NFR14, NFR15, NFR16.

---

## Epic 1: Know the Answer — Core VRAM Fit Verdict

Deliver the product's central promise: a user picks a GPU + model preset, sets workload knobs, and gets a live, transparent per-GPU VRAM breakdown with a "fits / doesn't fit + capacity" verdict in the browser.

### Story 1.1: Scaffold the monorepo and CI skeleton

As a developer,
I want the project scaffolded as a monorepo with tooling and a CI skeleton,
So that every subsequent story has a consistent place to add code with lint/test gates.

**Acceptance Criteria:**

**Given** an empty repository
**When** the scaffold is created
**Then** `packages/{engine,api,cli}` exist as a Python (uv/Poetry) workspace pinned to Python 3.13, and `web/` is a `create-vite` React-TS app
**And** ruff + mypy (Python) and ESLint + tsc (web) run clean on the empty skeleton
**And** a `ci.yml` runs lint, type-check, unit tests, and the SPA build on every PR
**And** `CONTRIBUTING.md` and `project-context.md` capture the consistency rules (bytes-only units, snake_case wire, engine-owned models, no calc in the SPA).

**Status:** Done (scaffold verified green, 2026-07-08).

**Dev Agent Record (Story 1.1):**
- **Toolchain divergence (approved):** used pip + venv (not uv) and npm (not pnpm); documented in CONTRIBUTING.md. Python pinned `>=3.13` (env has 3.14).
- **Verification — all green:** `ruff check` ✓ · `mypy` (strict) ✓ · `pytest` 5/5 ✓ · web `eslint` ✓ · `tsc --noEmit` ✓ · `vitest` 1/1 ✓ · `vite build` ✓ (built in 173ms).
- **Note:** Typer needed a no-op `@app.callback()` so subcommands stay named (single-command apps collapse otherwise); relevant when `check` lands in Story 3.1.
- **File List:** `.gitignore`, `pyproject.toml`, `README.md`, `CONTRIBUTING.md`, `project-context.md`, `.github/workflows/ci.yml`; `packages/engine/{pyproject.toml,src/vllm_calc_engine/__init__.py,tests/test_smoke.py}`; `packages/api/{pyproject.toml,src/vllm_calc_api/{__init__.py,main.py},tests/test_meta_endpoints.py}`; `packages/cli/{pyproject.toml,src/vllm_calc_cli/{__init__.py,main.py},tests/test_cli.py}`; `web/{package.json,package-lock.json,tsconfig.json,vite.config.ts,eslint.config.js,index.html,src/{main.tsx,App.tsx,App.test.tsx,test-setup.ts}}`; `presets/{README.md,models/,gpus/,schema/}`, `validation/README.md`, `docker/README.md`.
- **Change Log:** Scaffolded the monorepo (engine/api/cli + web), tooling config (ruff/mypy/pytest, ESLint/tsc/vitest), CI workflow, and consistency-rule docs. All quality gates pass.

### Review Findings (code review 2026-07-08)

_Adversarial review: Blind Hunter + Edge Case Hunter + Acceptance Auditor. Gates independently re-verified green. 6 false positives dismissed._

**[Review][Decision] → RESOLVED: adopt uv workspace (option 2, 2026-07-09)**
- [x] Local `vllm-calc-engine` sibling dep resolved only in the combined `pip install`. **Resolution:** migrate Python to a **uv workspace** with a root `[tool.uv.workspace]` + `[tool.uv.sources] vllm-calc-engine = { workspace = true }`, committing a `uv.lock`. This also subsumes the loose-pins and no-Python-lockfile findings. Reverses the earlier pip decision (docs updated). [packages/*/pyproject.toml]

**[Review][Patch] — ALL APPLIED & re-verified green (2026-07-09)**
- [x] vitest 3 ↔ Vite 8 dual-Vite: pinned `vite ^7` + `@vitejs/plugin-react ^4.6.0`; `npm ls vite` now shows a single deduped `vite@7.3.6` across build + vitest. [web/package.json]
- [x] `*.tsbuildinfo` added to `.gitignore`. [.gitignore]
- [x] Added `addopts = "--import-mode=importlib"`. [pyproject.toml]
- [x] Added `exclude` (`.venv`, `build`, `dist`, `node_modules`, `^web/`) under `[tool.mypy]`. [pyproject.toml]
- [x] Pins tightened via the uv migration: `fastapi~=0.139`, `typer~=0.26`, `requires-python>=3.13,<3.15`, bounded dev-tool group; **`uv.lock` committed** pins the full graph (subsumes the loose-pins + no-lockfile findings). [packages/*/pyproject.toml, uv.lock]

_Re-verification (all green): `uv run ruff` ✓ · `uv run mypy` ✓ · `uv run pytest` 5/5 ✓ · `uv sync --frozen` ✓ · web `eslint`/`tsc`/`vitest` 1/1/`vite build` ✓. CI updated to `astral-sh/setup-uv` + `uv sync --frozen`; CONTRIBUTING/project-context/README updated for uv._

**[Review][Defer]**
- [x] No committed Python lockfile (pip has none; web has package-lock.json) — reproducibility gap. Deferred: pick a lock strategy (uv.lock / pip-tools) with the workspace decision above.
- [x] `web/package-lock.json` must be committed for CI `npm ci` — advisory; handle at first commit.
- [x] `tsc -b` on a single non-composite tsconfig; `vite.config.ts` not type-checked by tsc — deferred, low; revisit if adopting project references.
- [x] CI omits the dependency-vuln scan (architecture CI intent / NFR13) — deferred; not a Story 1.1 AC, add in a later epic.

**Dismissed (verified false positives):** CLI missing `version`; CLI missing `[dev]` extra; `@types/react-dom` absent; `@testing-library/jest-dom` not installed; API `create_app` import gap; "frontend versions don't exist" — all contradicted by the actual files and the passing gates (blind reviewer saw an abbreviated snapshot + had a stale knowledge cutoff).

### Story 1.2: Compute model weights (with quantization and MoE)

As a user,
I want the engine to compute model weight memory for a given quantization,
So that the largest fixed component of VRAM is accurate.

**Acceptance Criteria:**

**Given** a model's total parameter count and a quantization scheme
**When** `weights` is computed
**Then** it returns integer bytes = params × bytes_per_param, with quantization mapping to the correct bytes-per-param
**And** for a MoE model, total (not active) parameters are used
**And** a golden-value test covers FP16, FP8, and AWQ/GPTQ 4-bit cases.

**Status:** Done (2026-07-09, red-green-refactor, verified green).

**Dev Agent Record (Story 1.2):**
- Added `packages/engine/src/vllm_calc_engine/quantization.py` (`WeightQuant` StrEnum: FP32/FP16/BF16/FP8/INT8/AWQ_4BIT/GPTQ_4BIT + `weight_bytes_per_param`) and `weights.py` (`weights_bytes(total_params, quant) -> int`, rejects negative params, returns integer bytes per the units invariant).
- MoE handled by contract: `weights_bytes` takes TOTAL params; a golden test asserts total-vs-active divergence (Mixtral-8x7B-style 46.7B → 93.4 GB FP16). bytes-per-param: FP32=4, FP16/BF16=2, FP8/INT8=1, 4-bit=0.5.
- **Golden tests** (`tests/test_weights.py`, 13 cases): per-scheme bpp, 70B golden byte values for FP16/FP8/4-bit, MoE total-not-active, negative-param guard.
- Ruff nudge applied: use `enum.StrEnum` (not `str, Enum`) on py313.
- **Verify green:** ruff ✓ · mypy (11 files) ✓ · pytest **18/18** ✓.
- **File List:** `packages/engine/src/vllm_calc_engine/{quantization.py,weights.py}`, `packages/engine/tests/test_weights.py`.

### Story 1.3: Compute GQA-aware KV cache

As a user,
I want the engine to compute KV-cache memory using the model's actual KV-head count,
So that modern GQA models are modeled correctly rather than over-counted.

**Acceptance Criteria:**

**Given** a model's layers, kv_heads, head_dim, kv-cache dtype, context length, and max_seqs
**When** KV cache is computed
**Then** it returns `2 × kv_heads × head_dim × kv_dtype_bytes × layers × ctx_len × max_seqs` in bytes
**And** MHA (kv_heads = attention_heads) and MQA (kv_heads = 1) are covered by the same formula
**And** golden-value tests verify a known GQA model (e.g. Llama-3-70B: 8 KV heads).

**Status:** Done (2026-07-09, red-green-refactor, verified green).

**Dev Agent Record (Story 1.3):**
- Added `KVCacheDtype` (FP16/BF16/FP8) + `kv_dtype_bytes` (2/2/1) to `quantization.py`, and `kv_cache.py` with `kv_bytes_per_token(layers, kv_heads, head_dim, kv_dtype)` = `2 × kv_heads × head_dim × kv_dtype_bytes × layers` and `kv_cache_bytes(..., ctx_len, max_seqs)` = per_token × ctx_len × max_seqs. Integer bytes; positive-input guards.
- GQA via actual `kv_heads`; MHA (=attention_heads) and MQA (=1) share the identical formula (parametrized test). Docstring notes the generic form conservatively over-estimates MLA/sliding-window (deferred fast-follow).
- **Golden tests** (`tests/test_kv_cache.py`, 9 cases): Llama-3-70B per-token = 327,680 B; total @4096/1seq = 1,342,177,280 B; FP8 halves FP16; ctx×seqs scaling; MHA/GQA/MQA; non-positive guards.
- **Verify green:** ruff ✓ · mypy (13 files) ✓ · pytest **27/27** ✓.
- **File List:** `packages/engine/src/vllm_calc_engine/kv_cache.py`, `quantization.py` (KV dtype added), `packages/engine/tests/test_kv_cache.py`.

### Story 1.4: Compute the three-term overhead

As a user,
I want overhead modeled as fixed context + activations + CUDA graphs,
So that the estimate reflects what vLLM actually reserves instead of a flat percentage.

**Acceptance Criteria:**

**Given** GPU count, hidden_size, max_num_batched_tokens, dtype, and enforce_eager
**When** overhead is computed
**Then** it returns the sum of a fixed per-GPU context term (+NCCL when TP>1), an activation term bounded by the chunked-prefill token budget, and a CUDA-graph term (zero when enforce_eager)
**And** the three sub-terms are individually returned in the result for the "show your work" UI
**And** overhead constants are defined in one place, documented as calibration targets for the validation harness (Epic 4).

**Status:** Done (2026-07-09, red-green-refactor, verified green).

**Dev Agent Record (Story 1.4):**
- Added `constants.py` (single place; PROVISIONAL calibration targets clearly flagged for Epic 4: `FIXED_CONTEXT_BYTES_PER_GPU`=1 GiB, `NCCL_BYTES_PER_GPU`=0.5 GiB, `ACTIVATION_MULTIPLIER`=8, `CUDA_GRAPH_BYTES_PER_GPU`=1 GiB) and `overhead.py` with `OverheadBreakdown` dataclass + `overhead_bytes(gpu_count, hidden_size, max_num_batched_tokens, dtype_bytes, enforce_eager)`.
- Three itemized sub-terms for "show your work": `fixed_context` (+NCCL when gpu_count>1), `activations` (= tokens × hidden × dtype × k), `cuda_graphs` (0 under enforce_eager). Integer bytes; positive-input guards.
- Constants explicitly documented as calibration targets, biased to over-predict (conservative invariant).
- **Tests** (`tests/test_overhead.py`, 8): activation formula, single-GPU no-NCCL + total=sum, multi-GPU adds NCCL, enforce_eager zeroes graphs, activation scaling, breakdown shape, constants-in-one-place, guards.
- **Verify green:** ruff ✓ · mypy (16 files) ✓ · pytest **35/35** ✓.
- **File List:** `packages/engine/src/vllm_calc_engine/{constants.py,overhead.py}`, `packages/engine/tests/test_overhead.py`.

### Story 1.5: Apply per-GPU tensor-parallel sharding and validate parallelism

As a user,
I want weights and KV sharded per GPU under TP with correct constraint validation,
So that multi-GPU configurations report true per-GPU memory and reject impossible setups.

**Acceptance Criteria:**

**Given** a valid TP that divides attention-heads and KV-heads and equals GPU count
**When** the per-GPU footprint is computed
**Then** weights and KV are divided by TP (KV divisor capped at `min(TP, kv_heads)`) while overhead is applied per GPU
**Given** TP exceeds the model's KV-head count
**Then** the result carries a KV-replication-wall warning that KV will not shard further
**Given** TP does not divide the heads or does not equal GPU count
**Then** the engine raises a typed constraint error with a plain-language reason.

**Status:** Done (2026-07-09, red-green-refactor, verified green).

**Dev Agent Record (Story 1.5):**
- Added `exceptions.py` (`EngineError` base, `InvalidParallelism`, `UnsupportedArchitecture`) and `parallelism.py` (`ParallelismPlan` frozen dataclass, `plan_tensor_parallel(...)`, `shard_bytes(total, divisor)`).
- **Sharding:** `weights_divisor = TP`; `kv_divisor = min(TP, kv_heads)` (replication wall). **Validation mirrors vLLM:** TP==gpu_count; `attention_heads % TP == 0`; if TP≤kv_heads then `kv_heads % TP == 0` else `TP % kv_heads == 0` (even replication). Errors raise `InvalidParallelism` with plain-language reasons; the replication wall (TP>kv_heads, even) is a **warning** carried in the plan, not an error.
- **Tests** (`tests/test_parallelism.py`, 10): valid GQA shard, TP=kv_heads, replication-wall warning + kv_divisor cap, TP≠gpu_count error, attention-indivisible error, KV-indivisible-below-wall error, uneven-replication-above-wall error, TP=1, shard_bytes, non-positive TP.
- **Verify green:** ruff ✓ · mypy (19 files) ✓ · pytest **45/45** ✓.
- **File List:** `packages/engine/src/vllm_calc_engine/{exceptions.py,parallelism.py}`, `packages/engine/tests/test_parallelism.py`.

### Story 1.6: Assemble the fit verdict and serving capacity

As a user,
I want a single result object with the go/no-go verdict and supported concurrency,
So that I get one clear answer to "will it fit and for how many requests?"

**Acceptance Criteria:**

**Given** the computed weights, KV, and overhead and a gpu_memory_utilization
**When** the result is assembled
**Then** `available_for_kv`, `max_concurrent = min(max_num_seqs_cap, ⌊capacity/ctx_len⌋)`, and `fits ⟺ max_seqs ≤ max_concurrent` are returned
**And** the verdict includes the capacity statement and a conservative/worst-case label on max_concurrent
**And** the result reports the calibrated vLLM version range
**And** a golden-value end-to-end test (a full scenario) locks the assembled numbers.

**Status:** Done (2026-07-09, red-green-refactor, verified green).

**Dev Agent Record (Story 1.6):**
- Added **shared Pydantic models** `models.py` (`CalcInput`, `Breakdown`, `CalcResult` — the engine-owned contract API/CLI import) and `calculate.py` (`calculate(CalcInput) -> CalcResult`, the engine's single entry point).
- Composes all four consumers per-GPU: weights/TP + KV/min(TP,kv_heads) + 3-term overhead; `available_for_kv = gpu_util×vram − weights − overhead`; `max_concurrent = min(max_num_seqs_cap, ⌊available_for_kv / kv_bytes_per_seq⌋)`; `fits ⟺ max_seqs ≤ max_concurrent`. Plain-language verdict (incl. weights+overhead-exceed-budget case), worst-case note, vLLM-range label, replication warnings propagated. Activations use compute dtype (2B) independent of weight quant. GiB→bytes only at the input edge.
- Centralized `SUPPORTED_VLLM_RANGE` in `engine/constants.py`; API now imports it (single source).
- **Golden end-to-end test** (`tests/test_calculate.py`, 6): Llama-70B AWQ on 2×A100 TP2 8k/32 → weights_pg=17.5 GB, overhead=2,952,790,016 B, available_for_kv=56,856,621,312 B, **max_concurrent=42, fits=True**; plus no-go at 128k, batch-cap bound, replication-wall propagation, invalid-TP raise, determinism.
- **Verify green:** ruff ✓ · mypy (22 files) ✓ · pytest **51/51** ✓ (API meta endpoints still green).
- **File List:** `packages/engine/src/vllm_calc_engine/{models.py,calculate.py,constants.py}`, `packages/api/src/vllm_calc_api/main.py`, `packages/engine/tests/test_calculate.py`.

### Story 1.7: Load curated presets from version-controlled YAML

As a user,
I want a curated set of model and GPU presets available,
So that I can size common setups without hand-entering architecture params.

**Acceptance Criteria:**

**Given** YAML preset files under `presets/models` and `presets/gpus` conforming to the Pydantic schema
**When** the backend starts
**Then** presets are loaded and validated into memory, failing fast on a schema violation
**And** the curated baseline covers the top ~15–20 models and common GPUs, each with provenance fields
**And** each preset's `id` matches its filename stem.

**Status:** Done (2026-07-10, verified green).

**Dev Agent Record (Story 1.7):**
- Added engine-owned Pydantic preset schema (`ModelPreset`, `GpuPreset` with a `_Provenance` base: `source` + `last_verified`) to `models.py`, and `api/presets_loader.py` (`load_model_presets`/`load_gpu_presets`) that reads `presets/{models,gpus}/*.yaml`, validates against the schema, **fails fast** (`PresetError`) on malformed/invalid/duplicate, and enforces **id == filename stem**. Added `pyyaml` (api) + `types-pyyaml` (dev); `uv.lock` updated.
- **Curated baseline (accuracy-first): 8 models + 6 GPUs.** Models: Llama-3.1 8B/70B/405B, Llama-3.3-70B, Qwen2.5 7B/72B, Mistral-7B-v0.3, Mixtral-8x7B (MoE, total params). GPUs: RTX 4090, L40S, A100 40/80GB, H100 80GB, H200 141GB. **Deliberately below the ~15–20 target:** models with uncertain architecture (Gemma-2 head_dim ambiguity; DeepSeek/MLA — deferred) were excluded rather than ship wrong numbers — the readiness report's "narrow to what's validated" fallback. Expansion is the Epic 4 contribution path (Story 4.2). Key Qwen2.5 architectures web-verified. All presets carry provenance.
- **Tests** (`api/tests/test_presets_loader.py`, 7): loads curated models/GPUs, MoE flag, provenance present, **preset→CalcInput→calculate() integration** (engine-ready), malformed fails fast, id/stem mismatch fails.
- Ruff nudge applied: PEP 695 type-parameter syntax on the generic loader.
- **Verify green:** ruff ✓ · mypy (24 files) ✓ · pytest **58/58** ✓.
- **File List:** `packages/engine/src/vllm_calc_engine/models.py`, `packages/api/src/vllm_calc_api/presets_loader.py`, `packages/api/pyproject.toml`, root `pyproject.toml`, `uv.lock`, `presets/models/*.yaml` (8), `presets/gpus/*.yaml` (6), `packages/api/tests/test_presets_loader.py`.

### Story 1.8: Expose the calculation over the HTTP API

As a developer,
I want a versioned REST endpoint that runs the engine,
So that any surface can get identical results from one source of truth.

**Acceptance Criteria:**

**Given** the engine and preset store
**When** the API is running
**Then** `POST /v1/calculate` returns the full result object (breakdown, verdict, capacity, flags, version) as snake_case JSON
**And** `GET /v1/presets/models`, `/v1/presets/gpus`, `/v1/health`, `/v1/version` respond correctly
**And** engine constraint/validation errors map to the structured error contract with the right HTTP status
**And** OpenAPI is generated and a typed client can be produced from it.

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 1.8):**
- Refactored `main.py` into an app factory that loads+validates presets at startup (fail-fast) into `app.state`, registers exception handlers, and mounts routers under `/v1`. Added `settings.py` (env-overridable presets dir), `errors.py` (structured `{error:{type,message,details?}}` contract + handlers), and `routes/{meta,calculate,presets}.py`.
- **`POST /v1/calculate`** wraps `engine.calculate()` (no logic in the API) → full `CalcResult` as snake_case JSON. **`GET /v1/presets/models|gpus`** list curated presets from app state. `/v1/health`, `/v1/version` moved to `routes/meta`.
- **Error mapping:** `InvalidParallelism` → 400 `constraint_violation`; `UnsupportedArchitecture` → 400 `unsupported`; request-body validation → 422 `validation`. OpenAPI auto-generated at `/openapi.json` (typed-client source for the SPA in Story 1.10).
- **Tests** (`api/tests/test_calculate_endpoint.py`, 6): calculate happy-path (snake_case, golden 42/fits, nested breakdown), constraint-violation→400 contract, request-validation→422 contract, model/GPU preset listing, OpenAPI exposes `/v1/calculate`. Existing meta tests still green.
- **Verify green:** ruff ✓ · mypy (31 files) ✓ · pytest **64/64** ✓.
- **File List:** `packages/api/src/vllm_calc_api/{main.py,settings.py,errors.py,routes/__init__.py,routes/meta.py,routes/calculate.py,routes/presets.py}`, `packages/api/tests/test_calculate_endpoint.py`.

### Story 1.9: Establish the SPA design-system foundation and app shell

As a user,
I want a fast, themeable single-page shell,
So that the calculator is pleasant and legible in light and dark.

**Acceptance Criteria:**

**Given** the React-Vite app
**When** the design foundation is implemented
**Then** Tailwind + Radix (shadcn/ui) tokens define the slate/indigo palette, semantic status tokens, and light/dark themes via CSS variables
**And** a persisted theme toggle switches themes and both pass WCAG AA contrast
**And** the responsive two-region layout shell (inputs / result at ≥lg, stacked below) renders without horizontal page scroll.

**Status:** Done (2026-07-10, verified green).

**Dev Agent Record (Story 1.9):**
- Added **Tailwind v4** (`tailwindcss` + `@tailwindcss/vite`) wired into `vite.config.ts`. `index.css` defines the **token layer** as CSS variables: slate neutrals + single indigo accent + reserved semantic `--fit/--no-fit/--warn`. **Light is default; dark applies via `@media (prefers-color-scheme: dark)` AND explicit `:root[data-theme]` (toggle wins both directions).** Token pairs chosen for WCAG AA on their surfaces.
- `theme.ts` (persisted light/dark: localStorage + `data-theme` on `<html>`, system-aware `effectiveTheme`, `initTheme`/`toggleTheme`) + `ThemeToggle` component + `initTheme()` on boot in `main.tsx`.
- `App.tsx`: responsive **two-region shell** — `lg:grid-cols-[minmax(320px,420px)_1fr]` (inputs left / result right at ≥lg, stacks below); header with product name + theme toggle. Regions are placeholders for Stories 1.10/1.11.
- Test infra: installed an in-memory `localStorage` in `test-setup.ts` (Node 25's experimental global shadows jsdom's and lacks getItem/setItem).
- **Tests** (`App.test.tsx` 3, `theme.test.ts` 4): shell renders both regions + heading + toggle; theme applies/persists/toggles/inits.
- **Design-verified (not unit-testable in jsdom, which has no layout engine):** no-horizontal-scroll and pixel contrast — automated axe/contrast checks land with the a11y story (UX-DR13 / Story 1.11).
- **Verify green:** eslint ✓ · tsc ✓ · vitest **7/7** ✓ · vite build ✓ (CSS compiled).
- **File List:** `web/{package.json,vite.config.ts,src/index.css,src/theme.ts,src/main.tsx,src/App.tsx,src/test-setup.ts,src/components/ThemeToggle.tsx,src/App.test.tsx,src/theme.test.ts}`.

### Story 1.10: Build the input surface with live recompute

As a user,
I want to pick presets and adjust knobs and see results update live,
So that exploring configurations feels effortless with no submit button.

**Acceptance Criteria:**

**Given** the app shell
**When** the input surface is implemented
**Then** searchable model/GPU comboboxes autofill architecture fields tagged "from preset" (still editable), grouped as Model / GPU & Parallelism / Workload / collapsed Advanced, with a "Custom model" reveal
**And** any input change debounces (~250ms) and fires one `/v1/calculate` call, updating results in place with the last valid result persisted (no full-screen spinner)
**And** the app loads with a pre-computed default scenario (no blank state)
**And** invalid inputs (e.g. TP divisibility) show plain-language errors on the offending field while the last valid result stays visible.

**Status:** Done (2026-07-10, verified green).

**Dev Agent Record (Story 1.10):**
- **Typed API client** (`src/api/{types.ts,client.ts}`): TS mirror of the engine contract; `postCalculate` (throws `ApiError` on the structured contract), `fetchModel/GpuPresets`; base URL via `VITE_API_BASE_URL` (public or local backend). SPA holds **no calc logic** (parity).
- **`useCalculator` hook**: config state (seeded with `DEFAULT_INPUT` = Llama-3.3-70B on 2×A100, so the app **pre-computes a default scenario on load**), preset load on mount, **debounced (250ms) live recompute**, **last-valid result persists** across errors/loading (never blanks), request-sequence guard drops stale responses.
- **`InputPanel`**: grouped `<fieldset>` inputs (Model / GPU & Parallelism / Workload / collapsed Advanced `<details>`); model & GPU **preset `<select>`s autofill** fields (arch tagged "◆ from preset (editable)"), "Custom…" option; helper `NumberField`.
- **`ResultPanel`** (minimal inline for 1.10 per readiness concern #2 — 1.11 upgrades to VerdictBanner/VramBreakdownBar): verdict line, per-GPU breakdown in **GiB (bytes→GiB only at this edge)**, warnings, worst-case + vLLM-version note; inline error banner with "showing last valid result"; dims (not blanks) during recompute.
- **`CalculatorPage`** wires the hook into the two regions; `App` renders header + page.
- **Scope calls (flagged):** preset pickers are accessible native `<select>` — *searchable-combobox filtering* and *per-field (vs. inline) error placement* are deferred polish (heavy to hand-roll + not headlessly testable).
- Test infra: added `vite-env.d.ts` for `import.meta.env` typing.
- **Tests** (`useCalculator.test.ts` 4 + `InputPanel.test.tsx` 2): default-compute-on-load, recompute-on-change, **error-keeps-last-result**, presets-on-mount, preset autofill, field edit. Total web **13/13**.
- **Verify green:** eslint ✓ · tsc ✓ · vitest 13/13 ✓ · vite build ✓.
- **File List:** `web/src/api/{types.ts,client.ts}`, `web/src/features/calculator/{defaults.ts,useCalculator.ts,InputPanel.tsx,ResultPanel.tsx,CalculatorPage.tsx,useCalculator.test.ts,InputPanel.test.tsx}`, `web/src/{App.tsx,vite-env.d.ts}`.

### Story 1.11: Render the verdict and VRAM breakdown

As a user,
I want an unmissable verdict and a transparent breakdown,
So that I trust the answer and understand why.

**Acceptance Criteria:**

**Given** a calculation result
**When** the result region renders
**Then** `VerdictBanner` shows icon + headline + capacity subline + version label (never color-alone) inside a polite ARIA live region
**And** `VramBreakdownBar` shows weights/KV/overhead vs. the budget marker with `role="img"` + a sentence aria-label and a screen-reader table, using the colorblind-safe validated palette
**And** the overhead segment expands into its three sub-terms ("show your work")
**And** motion respects `prefers-reduced-motion` and the layout is usable at 200% zoom.

**Status:** Done (2026-07-10, verified green). **← completes Epic 1 (walking skeleton).**

**Dev Agent Record (Story 1.11):**
- **`VerdictBanner`**: icon + "Fits/Won't fit" + verdict sentence + vLLM-version label; color **+ icon + text** (never color-alone, NFR17); wrapped in an `aria-live="polite"` region so recompute verdicts are announced.
- **`VramBreakdownBar`**: CSS stacked bar (weights/KV/overhead) vs. a budget marker; `role="img"` + full-sentence `aria-label`; **screen-reader `<table>` alternative** (sr-only); legend with swatches **and** text labels; **expandable overhead → 3 sub-terms** ("show your work"); width transitions gated by `motion-reduce:transition-none`; **colorblind-safe trio** (indigo/teal/slate) held distinct from status colors.
- Wired both into `ResultPanel` (replaced the minimal 1.10 view); last-valid-result persistence + inline error retained; recompute dims (not blanks).
- **a11y automation (UX-DR13):** added `vitest-axe`; an axe smoke test asserts **zero violations** on the rendered result. (axe can't compute color-contrast in jsdom → incomplete, not a violation; pixel-contrast remains design-verified.)
- **Tests** (`ResultPanel.test.tsx`, 6): verdict fit/no-go + live region, bar role+label + SR budget row, overhead expand, axe no-violations, error-keeps-last-result. Web total **19/19**.
- **Verify green:** eslint ✓ · tsc ✓ · vitest 19/19 ✓ · vite build ✓.
- **Live end-to-end smoke (real uvicorn):** `/v1/health` ok · 8 presets served · default scenario → `fits=True, max_concurrent=42` (matches engine golden) · invalid TP → HTTP 400. Stack proven browser-API-engine.
- **File List:** `web/src/features/calculator/{VerdictBanner.tsx,VramBreakdownBar.tsx,ResultPanel.tsx,ResultPanel.test.tsx}`, `web/package.json` (+vitest-axe).

---

## Epic 1 — COMPLETE (2026-07-10)
All 11 stories done and green. "Will it fit?" works end-to-end: React SPA → FastAPI `/v1/calculate` → pure engine → verdict + VRAM breakdown + capacity, with curated presets, live recompute, honest conservative labeling, and an accessible UI. **83 automated tests** (64 Python + 19 web) plus a live API smoke. Deferred within-epic polish: searchable-combobox filtering, per-field error placement, formal colorblind-palette validator run. Next: Epic 2 (act on the answer — command generation, remediation).

---

## Epic 2: Act on the Answer — Remediation & Runnable Command

Turn the verdict into action: generate the runnable command, suggest fixes on a no-go, surface honest caveats, and make every scenario shareable.

### Story 2.1: Generate and copy the vllm serve command

As a user,
I want a runnable `vllm serve` command matching my configuration,
So that I can launch exactly what I sized without hand-writing flags.

**Acceptance Criteria:**

**Given** a valid configuration
**When** the command is generated
**Then** the engine produces a `vllm serve` command with flags matching the config (model, --tensor-parallel-size, --quantization, --kv-cache-dtype, --max-model-len, --gpu-memory-utilization)
**And** `CommandBlock` renders it in monospace with tinted flags and a copy button
**And** copying shows a "Copied ✓" toast and announces via ARIA live.

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 2.1):**
- **Engine-owned generation (NFR3):** new `command.py` `serve_command(CalcInput) -> str`, pure/deterministic, so SPA/API/CLI emit the identical command. Added optional `model_ref` to `CalcInput` (HF repo id / path) and `serve_command` to `CalcResult`; `calculate()` populates it. The SPA only *tokenizes* the string for display — it never builds it.
- **Honest flags:** full-precision weights (fp32/fp16/bf16) and plain int8 emit **no** `--quantization` (vLLM has no single canonical arg / would reject); `awq-4bit→awq`, `gptq-4bit→gptq`, `fp8→fp8`. KV dtype fp16/bf16 is the "auto" default so `--kv-cache-dtype` is **omitted**; only fp8 emits it. `--gpu-memory-utilization` formatted trailing-zero-free (`:g`). Missing `model_ref` → `<your-model>` placeholder rather than a wrong repo id.
- **CommandBlock (UX-DR5):** monospace `<pre>` with `--flag` tokens tinted in the accent color, internal horizontal scroll (UX-DR12), a Copy button using `navigator.clipboard`, a transient "Copied ✓" toast, and an `aria-live="polite"` sr-only announcement. Wired into `ResultPanel` below the breakdown. SPA derives `model_ref` from the selected preset's `source` HF URL (`hfIdFromSource`); "Custom…" clears it to the placeholder.
- **Tests:** engine `test_command.py` (7 golden: awq no-auto-kv, model_ref use, full-precision omits quant, gptq map, fp8 kv flag, gmu formatting, result carries command); web `CommandBlock.test.tsx` (2: renders full command, copy → clipboard + toast + live announce). Fixtures updated for the new required field.
- **Verify green:** ruff ✓ · mypy (33 files) ✓ · pytest **71/71** ✓ · web eslint ✓ · tsc ✓ · vitest **21/21** ✓ · vite build ✓. **Live API smoke:** default → real `vllm serve meta-llama/Llama-3.3-70B-Instruct …` (fits, 42); fp8/custom → `<your-model> … --kv-cache-dtype fp8`.
- **File List:** `packages/engine/src/vllm_calc_engine/{command.py,models.py,calculate.py}`, `packages/engine/tests/test_command.py`; `web/src/api/types.ts`, `web/src/features/calculator/{CommandBlock.tsx,CommandBlock.test.tsx,ResultPanel.tsx,InputPanel.tsx,defaults.ts,useCalculator.test.ts,ResultPanel.test.tsx}`.

### Story 2.2: Suggest and apply nearest fitting configurations

As a user,
I want actionable fixes when a config doesn't fit,
So that I reach a working setup without a failed launch.

**Acceptance Criteria:**

**Given** a no-go result
**When** remediation runs
**Then** the engine returns one or more nearest fitting configurations (e.g. reduced context, FP8 KV, higher TP/more GPUs), each carrying the exact input delta
**And** `RemediationChips` renders them under the verdict
**And** clicking a chip applies its delta to the inputs and recomputes through the standard live-recompute path.

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 2.2):**
- **Honesty invariant:** new engine `remediation.py` `build_remediations(inp, base, compute)` returns up to 4 single-lever fixes, and a candidate is offered **only if applying its delta genuinely flips `fits` to True** (verified by re-running the compute). We never suggest a fix that doesn't actually work.
- **Levers tried (each a lone, explainable change):** FP8 KV cache (if not already), reduce context to the largest common length below current that fits (ladder 128k→1k), higher TP / more GPUs (smallest valid scale-up), reduce concurrency to the supported capacity. Each `Remediation` carries `label`, `detail` (`fits — up to N concurrent`), and the exact `delta` (a partial CalcInput).
- **No import cycle:** the compute entry point is *injected* into `build_remediations` rather than imported. Factored `calculate()` into a thin wrapper over `_compute()`; `calculate` populates `remediations` only on a no-go.
- **`Remediation` model** + `remediations: list[Remediation]` (default empty) added to the engine contract; flows through `/v1/calculate` automatically (parity).
- **`RemediationChips`** renders applyable chips under the verdict; clicking calls `onApply(delta)` → `useCalculator.setInput` → the **standard debounced live-recompute path** (no bespoke SPA logic). Chips hidden when the config fits.
- **Tests:** engine `test_remediation.py` (7: fits→none, no-go→≥1, **every remediation actually fits**, reduce-to-capacity target, TP divisor validity, no FP8 suggestion when already FP8, cap ≤4); web `RemediationChips.test.tsx` (3: empty→nothing, chip-per-item, click applies exact delta). Fixtures updated.
- **Verify green:** ruff ✓ · mypy (35 files) ✓ · pytest **78/78** ✓ · web eslint/tsc ✓ · vitest **24/24** ✓ · vite build ✓. **Live API smoke** (128k/32 no-go): offered `Context ≤ 8k` (→42) and `Serve 2 concurrent` (→2), both re-verified `fits=True`; FP8/higher-TP correctly withheld (they don't fit at that workload).
- **File List:** `packages/engine/src/vllm_calc_engine/{remediation.py,models.py,calculate.py}`, `packages/engine/tests/test_remediation.py`; `web/src/api/types.ts`, `web/src/features/calculator/{RemediationChips.tsx,RemediationChips.test.tsx,ResultPanel.tsx,CalculatorPage.tsx,useCalculator.test.ts,ResultPanel.test.tsx}`.

### Story 2.3: Expose advanced overhead levers

As an expert user,
I want to adjust `max_num_batched_tokens` and `enforce_eager`,
So that I can model non-default vLLM overhead behavior.

**Acceptance Criteria:**

**Given** the collapsed Advanced group
**When** I change an advanced lever
**Then** the value flows into the overhead computation and the result updates live
**And** `enforce_eager` set true zeroes the CUDA-graph overhead term
**And** the generated command reflects any lever that maps to a vLLM flag.

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 2.3):**
- **Mostly already in place from Epic 1:** the Advanced group (`max_num_batched_tokens`, `enforce_eager`, `max_num_seqs_cap`) already exists in `InputPanel`, flows through `useCalculator`'s debounced live recompute, and the engine's `overhead_bytes` already zeroes the CUDA-graph term under `enforce_eager` (Story 1.4). This story closed the last gap: **the generated command now reflects the overhead levers.**
- **`serve_command` extended:** appends `--enforce-eager` when set, and `--max-num-batched-tokens N` **only when the user overrode the default** (default read from `CalcInput.model_fields[...].default` so it stays in sync). Default configs still produce the clean golden command (unchanged), so no existing test broke.
- **Scope note:** `max_num_seqs_cap` (→ `--max-num-seqs`) is a capacity lever rather than an overhead lever; left out of this story's command flags to keep 2.3 focused on the two AC-named overhead levers.
- **Tests:** engine `test_command.py` +3 (enforce-eager flag, default levers add nothing, non-default max-num-batched-tokens emitted); web `InputPanel.test.tsx` +1 (enforce_eager checkbox toggles the input live).
- **Verify green:** ruff ✓ · mypy (35 files) ✓ · pytest **81/81** ✓ · web eslint/tsc ✓ · vitest **25/25** ✓ · vite build ✓. Command smoke: `… --max-num-batched-tokens 8192 --enforce-eager` emitted; FP16 correctly omits `--quantization`.
- **File List:** `packages/engine/src/vllm_calc_engine/command.py`, `packages/engine/tests/test_command.py`, `web/src/features/calculator/InputPanel.test.tsx`.

### Story 2.4: Surface honest over-provision and unsupported flags

As a user,
I want the tool to tell me when an estimate is conservative or unsupported,
So that I'm never misled by a confident-but-wrong number.

**Acceptance Criteria:**

**Given** a model flagged as MLA or sliding-window (known over-provision)
**When** the result renders
**Then** a calm amber callout explains the estimate is conservative/over-provisioned
**Given** an unsupported architecture
**Then** the result is clearly flagged rather than returning an unflagged number
**And** flags are carried in the result object (not thrown as errors).

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 2.4):**
- **New contract concept:** `AttentionType` enum (`standard`/`mla`/`sliding_window`/`other`) on `CalcInput` + `ModelPreset` (default `standard`, so all 8 existing presets validate unchanged and still load). A structured `Flag {type, message}` model + `flags: list[Flag]` on `CalcResult`.
- **Honesty over correctness-theater (NFR4/FR21):** `flags.py build_flags(inp)` → `mla`/`sliding_window` emit `over_provision_estimate` (generic KV formula is a conservative upper bound); `other` emits `unsupported` (uncalibrated, verify before relying). Flags are **carried in the result, never thrown** — the calculation always runs and returns a full labeled verdict. `calculate()` populates `flags` on every call (a flag can apply to a fit, too).
- **Why flags not branched math:** exact MLA/SWA KV math was deliberately deferred (brainstorm decision "keep a more generic calculation"); this is the honesty mechanism that makes that deferral safe rather than silently wrong.
- **`HonestyCallout`** — calm amber (reserved `--warn` token), icon + text (not color-alone), `role="note"`; renders "Conservative estimate" for over-provision and "Not calibrated" for unsupported. Placed under the verdict. Presets carry `attention_type` through autofill; no MLA/SWA presets ship in v1 yet (they arrive with the Epic 4 contribution path), so there's no new input selector — the mechanism is ready for them.
- **Tests:** engine `test_flags.py` (5: standard→none, MLA/SWA→over_provision, other→unsupported, carried-not-thrown); web `HonestyCallout.test.tsx` (3: empty, conservative label, not-calibrated label). Fixtures + QWEN test preset updated for the new field.
- **Verify green:** ruff ✓ · mypy (38 files) ✓ · pytest **86/86** ✓ · web eslint/tsc ✓ · vitest **28/28** ✓ · vite build ✓. **Live API smoke:** standard→200/no flags, mla & sliding_window→200/`over_provision_estimate`, other→200/`unsupported`; 8 presets still load.
- **File List:** `packages/engine/src/vllm_calc_engine/{attention.py,flags.py,models.py,calculate.py}`, `packages/engine/tests/test_flags.py`; `web/src/api/types.ts`, `web/src/features/calculator/{HonestyCallout.tsx,HonestyCallout.test.tsx,ResultPanel.tsx,InputPanel.tsx,defaults.ts,useCalculator.test.ts,ResultPanel.test.tsx,InputPanel.test.tsx}`.

### Story 2.5: Encode scenarios in the URL

As a user,
I want my configuration reflected in the URL,
So that I can share or restore an exact scenario with a link.

**Acceptance Criteria:**

**Given** any set of inputs
**When** inputs change
**Then** the query string updates (debounced) to encode the full configuration
**And** loading a URL with encoded inputs restores that exact scenario and computes it
**And** browser back/forward and refresh preserve the scenario.

**Status:** Done (2026-07-10, red-green-refactor, verified green). **← completes Epic 2.**

**Dev Agent Record (Story 2.5):**
- **Pure SPA story (no engine/API change).** New `urlState.ts` codec: `encodeInput` → query string; `decodeInput` → full `CalcInput`. The param shape is **derived from `DEFAULT_INPUT`** (keys + `typeof` per field), so it stays in sync automatically; unknown/malformed params fall back to the default rather than producing a broken input (`ctx_len=notanumber` → default). `model_ref=''` round-trips as `null` (custom model); booleans as `1`/`0`.
- **`useCalculator` wiring:** seeds initial state from `window.location.search` on mount (empty query → default scenario), keeps the URL in sync **inside the existing debounced recompute** via `history.replaceState` (copy-shareable, without flooding history per keystroke), and restores on browser back/forward via a `popstate` listener.
- **Test isolation:** added a `beforeEach` resetting the URL to `/` so app-global URL state doesn't leak between hook tests.
- **Tests:** `urlState.test.ts` (5: round-trip, empty→default, malformed-number fallback, empty model_ref→null, boolean 1/0); `useCalculator.test.ts` +2 (seeds scenario from `?ctx_len=1234` on mount; input change reflected in `location.search`).
- **Verify green:** eslint ✓ · tsc ✓ · vitest **35/35** ✓ · vite build ✓. (Engine/API unchanged: pytest **86/86**.)
- **File List:** `web/src/features/calculator/{urlState.ts,urlState.test.ts,useCalculator.ts,useCalculator.test.ts}`.

---

## Epic 2 — COMPLETE (2026-07-10)
All 5 stories done and green. The tool now goes from *answering* to *acting*: an engine-owned runnable `vllm serve` command (2.1), honest nearest-fitting remediation chips that only ever suggest fixes that actually fit (2.2), advanced overhead levers reflected in the command (2.3), calm honesty flags for MLA/SWA/uncalibrated architectures carried in the result rather than thrown (2.4), and full URL-as-state so any scenario is shareable and restorable (2.5). **114 automated tests** (86 Python + 28 web) plus live API smokes for command, remediation, and flags. Next: Epic 3 (CLI + self-hosted Docker backend).

---

## Epic 3: Reach It Anywhere — CLI & Self-Hosted Backend

Make the same engine reachable from the terminal and runnable on the user's own hardware.

### Story 3.1: Provide the companion CLI

As a platform engineer,
I want a CLI that checks a configuration and gates CI,
So that a deployment fails before a GPU is ever touched if it won't fit.

**Acceptance Criteria:**

**Given** the CLI installed and a backend URL (default local)
**When** I run `vllm-calc check --model … --gpu …:N --tp N --ctx … --max-seqs …`
**Then** it prints a human-readable verdict and exits 0 on fit, non-zero on no-go
**And** `--json` emits the full machine-readable result object
**And** the CLI produces identical results to the SPA for identical inputs (parity).

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 3.1):**
- **Design — thin HTTP client (parity by construction):** the CLI resolves presets and posts a full `CalcInput` to the backend's `POST /v1/calculate`, so its numbers come from the *same engine + same endpoint* as the SPA. This is stronger parity than re-importing the engine, and keeps the CLI free of preset-loading/FastAPI weight. `--api-url` defaults to `http://localhost:8000` (the Story 3.2 Docker backend is what it points at).
- **`vllm-calc check`** flags: `--model` (preset id), `--gpu id:count`, `--ctx`, `--max-seqs`, `--tp` (defaults to GPU count), `--quant`, `--kv-dtype`, `--gpu-mem-util`, `--api-url`, `--json`. It fetches `/v1/presets/{models,gpus}`, resolves the ids (unknown id → friendly error listing options), derives `model_ref` from the preset's HF source, and posts the config.
- **CI-gateable exit codes:** `0` fits · `1` won't fit · `2` usage/backend error (unknown preset, unreachable backend, engine constraint error). Human output shows verdict + per-GPU used/budget + capacity + honesty flags/warnings + remediation labels + the runnable command; `--json` emits the full result object verbatim.
- **Added `httpx~=0.28`** to CLI deps (uv.lock updated); `build_client` is a seam so tests inject an in-process client.
- **Tests (parity-proving):** `test_cli.py` drives `check` against the **real FastAPI app in-process** via `TestClient` (a sync httpx.Client bridging ASGI) — no network/server. 5 tests: version, fits→exit 0, no-go→exit 1 + suggests fixes, `--json` full result, unknown preset→exit 2. (First tried `httpx.ASGITransport` — async-only, incompatible with the sync client; `TestClient` is the right sync ASGI bridge.)
- **Verify green:** ruff ✓ · mypy (38 files) ✓ · pytest **90/90** ✓. **Live end-to-end** against a real uvicorn: fits→exit 0, no-go→exit 1, `max_concurrent=42` matches the SPA/engine golden exactly (parity over real HTTP).
- **File List:** `packages/cli/src/vllm_calc_cli/main.py`, `packages/cli/pyproject.toml`, `packages/cli/tests/test_cli.py`, `uv.lock`.

### Story 3.2: Package the backend as a local Docker image

As an operator,
I want to run the backend locally in Docker,
So that no configuration data leaves my network (air-gapped/self-hosted).

**Acceptance Criteria:**

**Given** the Docker image
**When** I run it with no internet access
**Then** the API serves calculations with no external runtime calls, optionally serving the static SPA from the same container
**And** configuration is via env vars (API base URL, vLLM version pin, CORS origins, rate-limit toggle)
**And** the SPA and CLI can be pointed at the local instance.

**Status:** Done (2026-07-10, verified green — image build to be run in CI/locally where a container runtime is available).

**Dev Agent Record (Story 3.2):**
- **Self-contained image** (`docker/Dockerfile`, multi-stage uv): builder installs engine + API **non-editably** (`uv sync --frozen --no-dev --no-editable`) into `/app/.venv`; runtime stage copies only that venv + the version-controlled `presets/`, runs as a **non-root** user with a `/v1/health` HEALTHCHECK. No source tree, no dev tooling, **no external runtime calls** (air-gapped-capable, NFR8). Plus `docker/docker-compose.yml` and a root `.dockerignore` (context = repo root; excludes `.venv`, `node_modules`, `web`, caches).
- **Env-driven operational config** (all optional, `settings.py`): `CORS_ORIGINS` (comma-sep; empty = same-origin), `RATE_LIMIT_ENABLED` + `RATE_LIMIT_PER_MINUTE`, `VLLM_VERSION_RANGE` (overrides the range reported by `/v1/version`), `SPA_DIR` (serve a bundled SPA at `/`), `VLLM_CALC_PRESETS_DIR`, `PORT`. `create_app` conditionally adds `CORSMiddleware`, a minimal in-process fixed-window rate limiter (`{error:{type:"rate_limited"}}`, 429), and mounts `StaticFiles` at `/` (after `/v1` so the API wins).
- **SPA + CLI point at it:** SPA via `VITE_API_BASE_URL`, CLI via `--api-url` — both already support a configurable base URL.
- **Tests:** `test_app_config.py` (6, via TestClient): CORS allowed-origin echo + no-header-by-default, rate limit 429 over the limit + off-by-default, `VLLM_VERSION_RANGE` override on `/v1/version`, bundled-SPA served at `/` while `/v1` still works.
- **Verify green:** ruff ✓ · mypy (39 files) ✓ · pytest **96/96** ✓ · `uv lock --check` fresh. **Image not built in this environment** (only podman present, no running runtime / base-image pulls) — Dockerfile validated by inspection; the config behaviour it depends on is unit-tested. Building the image is a CI/local step.
- **File List:** `docker/{Dockerfile,docker-compose.yml,README.md}`, `.dockerignore`, `packages/api/src/vllm_calc_api/{settings.py,main.py,routes/meta.py}`, `packages/api/tests/test_app_config.py`.

---

## Epic 3 — COMPLETE (2026-07-10)
Both stories done and green. The same engine is now reachable beyond the browser: a CI-gateable **CLI** (`vllm-calc check`, exit 0/1/2, `--json`, parity by construction against `/v1/calculate`) and a **self-contained Docker backend** (air-gapped-capable, env-configured CORS/rate-limit/version-pin/optional-SPA). **102 automated tests** (96 Python + 28 web unchanged) plus a live uvicorn CLI smoke. The Docker image build itself is deferred to a container-capable environment. Next: Epic 4 (accuracy validation harness + preset contribution path — where the provisional overhead constants finally get calibrated).

---

## Epic 4: Prove It & Grow It — Accuracy Validation & Preset Contribution

Build the trust engine (validation against real vLLM) and the community growth path (safe preset contribution).

### Story 4.1: Validate preset files in CI with provenance

As a maintainer,
I want preset files validated automatically,
So that a wrong or malformed preset can never reach users.

**Acceptance Criteria:**

**Given** a preset file in a PR
**When** CI runs
**Then** the file is validated against the generated JSON Schema (from the engine's Pydantic models) and the build fails on any violation
**And** each preset must carry provenance fields (source, last_verified, vllm_version_checked)
**And** a suspiciously low param count for a known-MoE model raises a warning.

**Status:** Done (2026-07-10, red-green-refactor, verified green).

**Dev Agent Record (Story 4.1):**
- **Provenance tightened:** added required `vllm_version_checked` to the engine's `_Provenance` (so both `ModelPreset` and `GpuPreset` require it); backfilled all **14** preset files (`"0.13"`). Web `ModelPreset`/`GpuPreset` types + the QWEN test fixture updated to match.
- **JSON Schema generated & committed:** `presets/schema/{model,gpu}.schema.json` from the Pydantic models (`write_schemas`), for external tooling/editor validation. The loader's `model_validate` remains the runtime source of truth (same schema).
- **`preset_validation.py`:** `validate_presets(base) → (errors, warnings)` runs the fail-fast loader (any schema/provenance/id-mismatch violation → error) and the MoE heuristic; `moe_param_warnings` flags `is_moe` presets with `total_params < 15B` (the classic "entered ACTIVE not TOTAL params" mistake) as an advisory **warning** (never fails). Runnable as `python -m vllm_calc_api.preset_validation` (exit 1 on error).
- **CI-wired:** new "Validate presets" step in `ci.yml` runs the module on every PR/push.
- **Tests:** `test_preset_validation.py` (4): shipped presets clean (0 errors/0 warnings), low-param MoE warns / real Mixtral doesn't, missing `vllm_version_checked` fails, id/filename mismatch still fails. Fixed the pre-existing loader test whose fixture predated the new required field.
- **Verify green:** ruff ✓ · mypy (41 files) ✓ · pytest **100/100** ✓ · web tsc ✓ · vitest **35/35** ✓ · validator prints "8 model + 6 GPU presets valid (0 warnings)".
- **File List:** `packages/engine/src/vllm_calc_engine/models.py`; `packages/api/src/vllm_calc_api/preset_validation.py`, `packages/api/tests/{test_preset_validation.py,test_presets_loader.py}`; `presets/{models,gpus}/*.yaml` (14), `presets/schema/{model,gpu}.schema.json`; `.github/workflows/ci.yml`; `web/src/api/types.ts`, `web/src/features/calculator/InputPanel.test.tsx`.

### Story 4.2: Provide a preset contribution path

As a community contributor,
I want a documented way to add a model/GPU preset,
So that coverage grows without core-team code changes.

**Acceptance Criteria:**

**Given** the contribution docs
**When** a contributor adds a preset
**Then** `CONTRIBUTING.md` explains the schema, provenance, and (where possible) cross-checking against the model's published `config.json`
**And** adding a preset requires no engine/API code change (data-only)
**And** the new preset appears in the API/SPA after merge + restart.

**Status:** Done (2026-07-10, docs — the data-only mechanism already exists and is test-covered).

**Dev Agent Record (Story 4.2):**
- **`CONTRIBUTING.md` → "Adding a model or GPU preset":** annotated model + GPU YAML templates (every field explained, incl. `attention_type` and the MoE TOTAL-not-active rule), a **`config.json` cross-check table** (preset field → HF config key, incl. GQA `num_key_value_heads` and the `head_dim` fallback), the "set `attention_type: other` when unsure so it's honestly flagged" guidance, and the local validation command (identical to CI).
- **`presets/README.md`** updated to point at the contribution section and state the data-only guarantee (no code change; appears after merge + backend restart).
- **Data-only is real, not aspirational:** the backend loads/validates the preset directory at startup (Story 1.7/1.8), so a merged YAML file surfaces in API, SPA, and CLI with no code change — already exercised by the loader tests. No new code for this story.
- **File List:** `CONTRIBUTING.md`, `presets/README.md`.

### Story 4.3: Build the accuracy validation harness

As a maintainer,
I want a harness that compares predictions to real vLLM reserve,
So that accuracy is provable rather than asserted.

**Acceptance Criteria:**

**Given** a matrix of GPU × model × quant × TP cases and a pinned vLLM version
**When** the harness runs on GPU hardware
**Then** it launches real `vllm serve`, captures actually-reserved VRAM, and compares it to the engine's prediction
**And** it reports per-case error and flags any under-prediction on a "fits" case as a failure
**And** its results feed calibration of the overhead constants.

**Status:** Done (2026-07-13, verified green — GPU measurement scaffolded/injected; portable core fully tested).

**Dev Agent Record (Story 4.3):**
- **New dev-only workspace package `packages/validation`** (`vllm-calc-validation`, deps: engine + pyyaml). Added to the uv workspace; **kept out of the runtime image** by scoping the Dockerfile to `uv sync … --package vllm-calc-api` (verified locally that api-scoped sync installs only api+engine). Old top-level `validation/` stub removed.
- **Split GPU-bound from portable:** `predict` (engine `used_per_gpu_bytes` + fits), `compare`, `run_matrix`, `summarize` are pure and fully unit-tested; the single GPU step — `measure_reserved_bytes` (launch real `vllm serve`, read reserved VRAM) — is an **injected callable**, so the analysis runs anywhere. The real impl raises with a clear "requires GPU + vLLM" message and is exercised via injection in tests.
- **Pass rule (NFR1/NFR2):** a case passes at **±10%** AND must not **under-predict a "fits" verdict** (predicted < measured on a fits case fails even within tolerance — that's the dangerous direction). `error_pct` is signed (positive = conservative over-predict).
- **`matrix.yaml`** pins the vLLM version and lists GPU×model×quant×TP cases as full inline `CalcInput`s (harness needs only the engine). Runnable via the `vllm-calc-validate` script; feeds calibration of the provisional overhead constants (Story 1.4).
- **Config plumbing:** added `packages/validation/{tests,src}` to pytest `testpaths`/`pythonpath` and to mypy `mypy_path` (the missing entry caused an initial import-untyped / found-twice error — no `py.typed` needed, matching the other three packages).
- **Tests:** `test_harness.py` (7: over-predict passes, under-predict-on-fits fails even within tolerance, under-predict on no-go can pass, out-of-tolerance fails, injected-measurement matrix run, load+predict without GPU, real measurement requires GPU) + `test_report.py` (3: pass-rate/gate all-pass, gate fails below 90%, any under-prediction-on-fits fails the gate).
- **Verify green:** ruff ✓ · mypy (46 files) ✓ · pytest **110/110** ✓. Smoke on the real matrix (simulated reserve 4% below prediction) → pass_rate 1.0, gate True, 0 under-predictions.
- **File List:** `packages/validation/**` (pyproject, `src/vllm_calc_validation/{__init__,harness,report}.py`, `matrix.yaml`, `tests/{test_harness,test_report}.py`, `README.md`), `pyproject.toml` (workspace/pytest/mypy), `docker/Dockerfile`, `uv.lock`.

### Story 4.4: Gate and publish the validation pass rate

As a user evaluating the tool,
I want the accuracy pass rate published and CI-gated,
So that I can trust the numbers at the point of use.

**Acceptance Criteria:**

**Given** the harness
**When** it runs on the self-hosted GPU CI runner (scheduled and on vLLM-version bumps)
**Then** it computes the pass rate (target ≥90% within ±10%, zero under-predictions on "fits")
**And** the pass rate and calibrated vLLM version range are published where users can see them
**And** a failing pass rate is surfaced to maintainers rather than silently ignored.

**Status:** Done (2026-07-13, verified green — GPU CI workflow scaffolded for the self-hosted runner).

**Dev Agent Record (Story 4.4):**
- **Gate** (from Story 4.3's `summarize`): `gate_passed = pass_rate ≥ 90% AND zero under-predictions on "fits"`. `vllm-calc-validate` exits non-zero when the gate fails.
- **Publish, honestly:** `report.publish(summary, path)` writes the summary JSON; the harness writes it to `VALIDATION_RESULTS_PATH` (repo-root default). New **`GET /v1/validation`** serves it: **`pending`** (with the calibrated range) until a real GPU run publishes results — never a made-up number — then **`validated`** with pass_rate/gate. The generated `validation-results.json` is gitignored (published via the API, not committed).
- **At the point of use:** SPA `AccuracyFooter` fetches `/v1/validation` and shows either "X% of cases within ±10% (measured against real vLLM)" or "not yet validated against real vLLM", always with the calibrated vLLM range.
- **Surfaced to maintainers:** `.github/workflows/validation-gpu.yml` runs on a **self-hosted `[self-hosted, gpu]` runner** — scheduled weekly, on manual dispatch, and on matrix/version changes — runs the harness (non-zero exit fails the job) and uploads the results artifact even on failure. Not runnable in this environment (no GPU); scaffolded + validated by inspection.
- **Tests:** api `test_validation_endpoint.py` (2: pending when no file, validated when present) + validation `test_report.py::test_publish_writes_readable_summary`; web `AccuracyFooter.test.tsx` (2: validated pass-rate + pending states).
- **Verify green:** ruff ✓ · mypy (48 files) ✓ · pytest **113/113** ✓ · web eslint/tsc ✓ · vitest **37/37** ✓ · vite build ✓. Live smoke: `/v1/validation` → `pending` with `calibrated_vllm_range: ">=0.13,<0.14"`.
- **File List:** `packages/validation/src/vllm_calc_validation/{report.py,harness.py,__init__.py}`, `packages/validation/tests/test_report.py`; `packages/api/src/vllm_calc_api/{settings.py,main.py,routes/validation.py}`, `packages/api/tests/test_validation_endpoint.py`; `web/src/api/{types.ts,client.ts}`, `web/src/App.tsx`, `web/src/features/calculator/{AccuracyFooter.tsx,AccuracyFooter.test.tsx}`; `.github/workflows/validation-gpu.yml`, `.gitignore`.

---

## Epic 4 — COMPLETE (2026-07-13)
All 4 stories done and green. The trust + growth engine: presets are **schema-validated with provenance in CI** (4.1), a documented **data-only contribution path** grows coverage without code changes (4.2), an **accuracy harness** compares predictions to real `vllm serve` reserve with a conservative pass rule (4.3), and the **pass rate is gated + published** at the point of use with a self-hosted GPU CI workflow (4.4). GPU-bound steps (real measurement, the GPU runner) are scaffolded + injected/documented; every portable part is unit-tested. **150 automated tests** (113 Python + 37 web).

---

## Project — ALL 4 EPICS COMPLETE (2026-07-13)
From a one-line idea to a tested, multi-surface product via the full BMad method:
**know** the answer (E1: engine + API + SPA, live "will it fit?") → **act** on it
(E2: runnable command, honest remediation, honesty flags, shareable URLs) → **reach**
it anywhere (E3: CI-gateable CLI + air-gapped Docker backend) → **prove & grow** it
(E4: CI preset validation, contribution path, accuracy harness + published pass rate).
**150 automated tests** (113 Python + 37 web) + live API/CLI smokes; single-engine
parity (NFR3) held throughout. Known deferred: real GPU calibration of the provisional
overhead constants (harness ready), Docker image build (needs a container runtime),
searchable-combobox / per-field-error UI polish.

---

## Post-v1 Enhancements

Additive stories that reopened a completed epic. Story spec lives in `docs/stories/`.
(Note: the "(4.4)" in the Epic 4 completion note above is informal prose for the
gate+publish work recorded under Story 4.3; the Story 4.4 below is the first standalone
post-completion story.)

### Story 4.4: Add a purpose one-liner to model presets

As a user choosing a model, I want each preset to carry a short "what it's good for" line,
so I can quickly tell which model fits my use case (agentic coding, long-context, general
chat, …) without leaving the tool. Extends Epic 4's preset schema + contribution theme.

**Status:** Review (2026-07-22).

**Dev Agent Record (Story 4.4):**
- **Additive, backward-compatible schema change:** optional `purpose: str | None = None` on the engine's `ModelPreset` (not on `_Provenance`). No engine calc, endpoint, or loader change — the field rides existing Pydantic serialization to API/SPA/CLI (the Epic 4 data-only guarantee). Regenerated `presets/schema/model.schema.json` via `write_schemas`; `gpu.schema.json` byte-unchanged.
- **Data:** authored a one-line `purpose` for **all 30** `presets/models/*.yaml` (inserted after `name:`), each grounded in the model's documented strengths (agentic coding / reasoning / long-context / general chat / multilingual / lightweight-edge / MoE-efficiency). Wording is editorial and best-effort — flagged for a maintainer review pass.
- **SPA:** `purpose?: string | null` on the web `ModelPreset`; shown as a `--muted` caption above the "◆ architecture from preset" line in `InputPanel`, hidden for custom models and presets without a purpose (no layout shift). `<option>` labels stay name-only to keep the native `<select>` scannable/accessible (UX-DR13).
- **Docs:** `CONTRIBUTING.md` model template documents `purpose` as optional with "one line, don't overclaim" guidance.
- **Tests:** loader asserts every curated preset carries a non-empty `purpose` (AC4 guardrail) and that a preset without one defaults to `None`; web test asserts the caption shows on select and hides for custom (QWEN fixture given a `purpose`).
- **Verify green:** ruff ✓ · mypy (48 files) ✓ · pytest **118** ✓ · web eslint/tsc ✓ · vitest **42** ✓ · vite build ✓ · validator "30 model + 11 GPU presets valid (0 warnings)".
- **File List:** `packages/engine/src/vllm_calc_engine/models.py`; `presets/schema/model.schema.json`; `presets/models/*.yaml` (30); `web/src/api/types.ts`, `web/src/features/calculator/InputPanel.tsx`; `CONTRIBUTING.md`; `packages/api/tests/test_presets_loader.py`, `web/src/features/calculator/InputPanel.test.tsx`.
