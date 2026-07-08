---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-07-08'
inputDocuments:
  - docs/prd.md
  - docs/product-brief-vllm-calc.md
  - docs/product-brief-vllm-calc-distillate.md
  - spec.txt
  - docs/brainstorming/brainstorming-session-2026-07-01.md
workflowType: 'architecture'
project_name: 'vllm-calc'
user_name: 'Simon'
date: '2026-07-08'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:** 32 FRs across 8 capability areas. Architecturally they collapse into three concerns: (1) a **pure calculation engine** (FR6–FR17: VRAM math, TP sharding, capacity, remediation, command generation) — deterministic, side-effect-free; (2) **delivery surfaces** (FR23–FR27: SPA, HTTP API, CLI) that must produce identical results; (3) **preset & validation subsystems** (FR1–FR2, FR28–FR32: flat-file preset store, schema validation, and a vLLM-launching accuracy harness).

**Non-Functional Requirements:** 17 NFRs. The dominant driver is **Accuracy & Correctness** (NFR1–NFR4): determinism, cross-surface parity, conservative bias, and honest-failure flagging — these push toward a pure, versioned, golden-tested engine. **Portability** (NFR8–NFR9: self-contained Docker, static SPA, no external runtime calls) rules out cloud-only dependencies. Performance targets (NFR5–NFR7) are easily met by in-process math. Security is minimal (no auth, no PII); maintainability demands an **extensible engine** (NFR14) and **flat-file presets** (NFR15).

### Scale & Complexity
- Primary domain: **Full-stack** (Python/FastAPI API + static SPA + Python CLI)
- Complexity level: **Medium** — simple stateless runtime; sophistication concentrated in engine correctness + CI validation harness, not distributed systems
- Estimated architectural components: **~5** — (1) calculation engine (core package), (2) HTTP API, (3) SPA, (4) CLI, (5) preset store + schema/validation, with the validation harness as a CI-only sixth

### Technical Constraints & Dependencies
- Python/FastAPI backend; version-controlled flat-file presets; Docker-packaged, locally-runnable, air-gapped-capable; no database, no auth, no session state in v1.
- Hard external coupling to **vLLM's runtime memory behavior**, which is version-sensitive → results must be pinned/labeled to a supported vLLM version range.
- Validation harness requires real GPU hardware + a vLLM install; runs in CI, not in the shipped product.

### Cross-Cutting Concerns Identified
- **Calculation parity** across SPA/CLI/API (single shared engine is the guarantor).
- **vLLM version coupling** — engine + results declare their calibrated version range.
- **Preset integrity** — schema validation in CI; provenance tracking; guard against silent rot.
- **Honest failure** — flag over-provision (MLA/SWA) / unsupported architectures rather than returning confident-wrong numbers.

## Starter Template Evaluation

### Primary Technology Domain
Full-stack: **Python backend (FastAPI) + static React SPA (Vite) + Python CLI (Typer)**, organized as a single monorepo. No single full-stack starter template is used — deliberately composed from minimal, official scaffolds to avoid carrying features we explicitly don't want (auth, database, user management).

### Starter Options Considered
- **Opinionated full-stack templates** (e.g. FastAPI full-stack template with Postgres/auth/users): rejected — they bundle a database, auth, and user management that contradict our stateless/no-auth/no-DB v1. More to strip out than to build.
- **Minimal composition (chosen):** official `create-vite` React-TS scaffold for the SPA + a hand-rolled FastAPI app + a Typer CLI, in a monorepo. Maximum control, nothing to remove, each piece independently upgradable.

### Selected Approach: Minimal Composed Monorepo

**Rationale:** The runtime is intentionally simple (stateless, no DB, no auth). The value is concentrated in the calculation engine, so the scaffold should add zero conceptual overhead. Composing official minimal scaffolds keeps the dependency surface small (supports the air-gapped/Docker goal) and each surface upgradable on its own.

**Repository layout (proposed):**
```
vllm-calc/
├── packages/
│   ├── engine/        # pure Python calc engine (spec.txt model) — importable package, the single source of truth
│   ├── api/           # FastAPI app (imports engine) + preset loading
│   └── cli/           # Typer CLI (thin client of the API; or imports engine directly for offline)
├── web/               # React + Vite + TS SPA (static build, configurable API base URL)
├── presets/           # version-controlled flat-file model & GPU presets (JSON/YAML) + schema
├── validation/        # CI-only harness: launches real vllm serve, compares predicted vs actual
└── docker/            # Dockerfile(s) for the locally-runnable backend
```

**Initialization commands (pinned to current stable, verified July 2026):**
```bash
# SPA
npm create vite@latest web -- --template react-ts     # Vite 8.x, React 19.2.x

# Backend + CLI (Python 3.13; managed with uv or Poetry)
#   fastapi ~=0.139   (released 2026-07-01, supports Python 3.10–3.14)
#   typer   ~=0.26    (vendors Click since 0.26)
#   pydantic v2 for models/validation (FastAPI + Typer share it)
```

**Architectural decisions provided / pinned by this stack:**
- **Language & Runtime:** Python **3.13** (backend, CLI, engine, harness — one ecosystem); Node **20.19+/22.12+** (Vite 8 build only), TypeScript for the SPA.
- **Backend:** FastAPI **~=0.139** + Uvicorn; Pydantic **v2** for request/response models and preset schema validation.
- **CLI:** Typer **~=0.26** (Click vendored), shares Pydantic models with the API.
- **Frontend:** React **19.2.x** + Vite **8.x** + TypeScript; static build, no SSR (SPA points at a configurable API base URL).
- **Visualization:** the VRAM breakdown is a simple stacked bar — start with hand-rolled SVG/CSS (zero-dep, boring); adopt a charting lib only if the "Rule of Three" is met.
- **Package management / monorepo:** `uv` (or Poetry) for Python workspaces; `pnpm` for the web package. Engine published as an internal package imported by API and CLI — the parity guarantor.
- **Testing:** `pytest` (engine golden-value + property tests, API), `vitest` (SPA); ruff for Python lint/format, ESLint/Prettier for web.

**Note:** Project initialization via these commands should be the first implementation story.

**Version sources (verified July 2026):** [Vite releases](https://vite.dev/releases) · [React versions](https://react.dev/versions) · [FastAPI on PyPI](https://pypi.org/project/fastapi/) · [Typer on PyPI](https://pypi.org/project/typer/) · [Python downloads](https://www.python.org/downloads/)

## Core Architectural Decisions

### Decision Priority Analysis
**Critical (block implementation):** engine-as-shared-package, calc-via-API (parity), preset format & loading, API contract shape, Docker packaging.
**Important (shape architecture):** SPA state/URL strategy, error-handling contract, CI topology for the GPU validation harness.
**Deferred (post-MVP):** rate limiting hardening, anonymous telemetry, CDN/split hosting of the public instance.

### Data Architecture
- **No database.** State is limited to in-memory presets loaded at startup; each calculation is stateless.
- **Presets = version-controlled YAML files** under `presets/`, one file (or grouped files) per model/GPU, each carrying provenance fields (`source`, `last_verified`, `vllm_version_checked`). Loaded into memory on backend startup.
- **Schema source of truth = Pydantic v2 models.** JSON Schema is generated from them for docs + CI validation. Custom presets submitted inline in a request are validated by the same models — never persisted.
- **Engine data flow:** pure functions in `packages/engine`, input/output as Pydantic models; zero I/O, zero global state (guarantees determinism, NFR3).

### Authentication & Security
- **No authentication, no accounts** (v1).
- **Input validation** at the API boundary via Pydantic (rejects malformed/at-risk configs with structured errors); no execution of user-supplied content.
- **CORS** configured to allow the public SPA origin; self-hosted deployments configure their own.
- **Rate limiting:** light IP-based limit on the *public* instance only (abuse guard), via middleware (e.g. SlowAPI); off for self-hosted. Minimal/deferrable.
- **Supply chain:** dependency-vulnerability scanning + lockfiles in CI.

### API & Communication Patterns
- **REST + JSON, versioned `/v1`.** Stateless. Primary endpoint `POST /v1/calculate` returns the full result object (per-GPU breakdown, verdict, capacity, remediation suggestions, generated `vllm serve` command, honesty flags, calibrated vLLM version range) in one call.
- **Preset endpoints:** `GET /v1/presets/models`, `GET /v1/presets/gpus`; `GET /v1/health`, `GET /v1/version`.
- **OpenAPI auto-generated by FastAPI** — the contract for typed client generation in the SPA and a sanity check for the CLI.
- **Error contract:** structured error model distinguishing *validation errors* (bad input), *constraint violations* (e.g. TP doesn't divide heads), and *unsupported/over-provision* flags — so surfaces render honest messages (NFR4) rather than a generic 400.

### Frontend Architecture
- **React 19 + Vite + TS**, single-page, static build. **Calc via debounced API calls** (~200–300ms debounce) → engine parity preserved (NFR3).
- **State:** minimal — React local state + a thin fetch hook (TanStack Query optional; Rule of Three before adding it). **Input state encoded in URL query params** from day one — cheap, and groundwork for the shareable-scenario fast-follow.
- **Visualization:** hand-rolled SVG/CSS stacked bar for weights/KV/overhead vs. budget; non-color-only fit encoding (NFR17). Charting library only if complexity grows.
- **API base URL configurable** (build/runtime env) so the same SPA points at the public API or a local backend.

### Infrastructure & Deployment
- **Single Docker image** serves the FastAPI backend and, optionally, the static SPA via FastAPI `StaticFiles` — a **one-container** self-host story (backend + UI, air-gapped). Public instance may split (SPA on static/CDN host, backend on a small container host) — an ops choice, not an architecture change.
- **Config via environment variables** (SPA API base URL, pinned vLLM version, CORS origins, rate-limit toggle). No secrets in v1.
- **CI/CD = GitHub Actions**, two tiers: (1) **every PR** — lint, unit/golden engine tests, SPA build, **preset schema validation**; (2) **GPU validation harness** on a **self-hosted GPU runner**, run on a schedule and on vLLM-version bumps (not per-PR — needs real hardware + model downloads).
- **Observability:** structured logs, no PII/request-content persistence on the public instance (NFR12); optional anonymous aggregate telemetry, opt-in.

### Decision Impact Analysis
**Implementation sequence:** (1) engine package + golden tests → (2) preset schema + loader → (3) FastAPI `/calculate` over the engine → (4) CLI over the API → (5) SPA → (6) Docker packaging → (7) validation harness + CI wiring.
**Cross-component dependencies:** the **engine package is the linchpin** — API, CLI, and validation harness all import it; its Pydantic I/O models are the contract the SPA (via OpenAPI) and CLI depend on. Changing the engine's result model ripples to all surfaces, so it's versioned deliberately.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined
**Critical conflict points identified:** ~7 areas — most importantly the **cross-language casing boundary** (Python snake_case ↔ JSON ↔ TS camelCase) and **units** (bytes vs GB vs GiB), which for a VRAM calculator is a correctness hazard, not just a style nit.

### The Units Rule (project-critical)
- **The engine computes exclusively in bytes (integer).** No GB/GiB math inside the engine. Ever.
- **Conversion happens only at the presentation edge** (SPA formatting, CLI output). GPU VRAM is interpreted as **GiB (1024³)** unless a preset explicitly says otherwise; displayed values state their unit.
- Rationale: mixing GiB/GB (a ~7% difference) or bytes/GB inside the math is exactly the class of silent error that would violate the conservative-accuracy invariant.

### Naming Patterns
- **Python:** `snake_case` functions/variables, `PascalCase` classes/Pydantic models, modules `snake_case.py`. Pure engine functions are verbs (`compute_kv_cache`, `assess_fit`).
- **TypeScript/React:** `camelCase` variables/functions, `PascalCase` components + files (`VramBar.tsx`), hooks `useX`.
- **API JSON:** **`snake_case` field names on the wire** (matches Python/Pydantic naturally); the SPA maps to camelCase at its boundary via the generated OpenAPI client. One rule end-to-end, no ambiguity.
- **API routes:** plural nouns, lower-kebab where multi-word, path params `{id}` style — e.g. `/v1/presets/models`, `/v1/calculate`.
- **Presets:** filenames kebab-case by canonical id (`llama-3.3-70b.yaml`, `a100-80gb.yaml`); preset `id` fields match the filename stem.

### Structure Patterns
- **Tests co-located per package** under `tests/` within each package (`packages/engine/tests/`), mirroring source layout; golden-value fixtures for the engine live in `packages/engine/tests/golden/`.
- **Shared Pydantic models** (calc input/output, preset schema) live in the **engine package** and are imported by API and CLI — never redefined. This is the parity contract.
- SPA organized **by feature** (`web/src/features/calculator/…`), shared UI in `web/src/components/`.

### Format Patterns
- **API success:** return the resource/result object **directly** (no `{data:…}` envelope) — FastAPI + OpenAPI idiom.
- **API errors:** single structured model `{ error: { type, message, details? } }` where `type ∈ {validation, constraint_violation, unsupported, over_provision_estimate, internal}`; HTTP 422 for input validation, 200-with-flags for honest over-provision estimates (it's a *result*, not an error), 400 for constraint violations.
- **Numbers:** integers for byte quantities; the result object carries both raw bytes and pre-formatted display strings so all surfaces render identically.
- **Booleans** literal `true/false`; **null** for "not applicable" (e.g. `sliding_window: null`).

### Communication & State Patterns
- **SPA state:** immutable updates; input state is the single source, mirrored to URL query params; API calls are debounced and their results treated as derived (never stored as duplicated source of truth).
- **Loading/error UI:** every calc call has explicit states — `idle/loading/result/error`; the verdict area renders skeleton on loading, never stale-with-no-indicator.

### Process Patterns
- **Engine purity:** engine functions raise typed domain exceptions (`UnsupportedArchitecture`, `InvalidParallelism`) — they never print, log, or do I/O. The API layer translates these to the error contract.
- **Honest-failure flags** are carried in the *result*, not thrown — so a calculable-but-over-provisioned answer (MLA) returns a value **plus** a flag (NFR4).
- **Logging:** structured (JSON) at the API/CLI layer only; levels `INFO` for requests (no request content on public instance), `WARNING` for flagged estimates, `ERROR` for internal faults.

### Enforcement Guidelines
**All contributors/agents MUST:** compute in bytes; import shared models from the engine (never redefine); use snake_case on the API wire; return results-with-flags rather than throwing for over-provision; co-locate tests; keep the engine I/O-free.
**Enforcement:** ruff + mypy (strict) on Python, ESLint/tsc on web, a golden-value test suite as the behavioral contract, and preset schema validation — all CI-gated. A `CONTRIBUTING.md` + generated `project-context.md` will encode these rules for future AI agents.

### Anti-Patterns (do NOT)
- ❌ Doing GB/GiB arithmetic inside the engine, or passing floats-of-GB between functions.
- ❌ Re-implementing the calc in TypeScript for the SPA (breaks parity — the whole moat).
- ❌ Throwing an exception for an over-provisioned/MLA estimate (it's a flagged result).
- ❌ Duplicating the input/output models in the API or CLI instead of importing from the engine.

## Project Structure & Boundaries

### Complete Project Directory Structure
```
vllm-calc/
├── README.md
├── CONTRIBUTING.md                 # encodes the consistency rules for humans + AI agents
├── project-context.md              # AI-agent rules (units, parity, snake_case wire, etc.)
├── LICENSE                         # OSS license
├── pyproject.toml                  # uv/Poetry workspace root (engine, api, cli)
├── pnpm-workspace.yaml             # web package
├── .github/
│   └── workflows/
│       ├── ci.yml                  # PR: lint, type-check, unit/golden tests, SPA build, preset validation
│       └── validation-gpu.yml      # self-hosted GPU runner: real vllm serve vs predicted (scheduled + on vLLM bump)
├── packages/
│   ├── engine/                     # THE calculation core (pure, deterministic, I/O-free)
│   │   ├── src/vllm_calc_engine/
│   │   │   ├── models.py           # Pydantic v2 I/O models — the shared contract (imported everywhere)
│   │   │   ├── weights.py          # weights = params × bytes_per_param (MoE = total params)
│   │   │   ├── kv_cache.py         # GQA-aware KV; attention-type dispatch (registry, extensible)
│   │   │   ├── overhead.py         # 3-term overhead (fixed ctx + activations + cuda graphs)
│   │   │   ├── parallelism.py      # per-GPU TP sharding + KV-replication wall
│   │   │   ├── capacity.py         # max_concurrent, fits ⟺ max_seqs ≤ max_concurrent
│   │   │   ├── remediation.py      # nearest-fitting-config search
│   │   │   ├── command.py          # vllm serve command generation
│   │   │   ├── quantization.py     # quant scheme → bytes (weights + KV); registry
│   │   │   ├── units.py            # bytes-only helpers + edge conversion (GiB)
│   │   │   └── exceptions.py       # UnsupportedArchitecture, InvalidParallelism, …
│   │   └── tests/
│   │       ├── golden/             # golden-value fixtures = behavioral contract
│   │       └── test_*.py           # unit + property tests
│   ├── api/                        # FastAPI app (imports engine)
│   │   ├── src/vllm_calc_api/
│   │   │   ├── main.py             # app factory, CORS, error handlers, static-file mount (optional)
│   │   │   ├── routes/
│   │   │   │   ├── calculate.py     # POST /v1/calculate
│   │   │   │   ├── presets.py       # GET /v1/presets/{models,gpus}
│   │   │   │   └── meta.py          # GET /v1/health, /v1/version
│   │   │   ├── presets_loader.py    # loads + validates YAML presets into memory at startup
│   │   │   ├── errors.py            # engine exceptions → error contract
│   │   │   └── settings.py          # env config (CORS, vLLM version pin, rate-limit toggle)
│   │   └── tests/
│   └── cli/                        # Typer CLI (thin API client; can import engine for offline)
│       ├── src/vllm_calc_cli/
│       │   ├── main.py             # `vllm-calc check …` (--json, non-zero exit on no-go)
│       │   └── client.py           # HTTP client to a configurable/local backend
│       └── tests/
├── web/                            # React + Vite + TS SPA (static)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── api/                    # generated OpenAPI client + thin fetch/debounce hook
│   │   ├── features/calculator/    # inputs, verdict, remediation, command panels
│   │   ├── components/             # VramBar (SVG stacked bar), shared UI
│   │   └── lib/                    # URL-state (query params), formatting (bytes→GiB display)
│   └── tests/                      # vitest
├── presets/                        # version-controlled flat-file presets (YAML)
│   ├── models/                     # llama-3.3-70b.yaml, qwen2-72b.yaml, deepseek-v3.yaml, …
│   ├── gpus/                       # a100-80gb.yaml, h100-80gb.yaml, l40s.yaml, …
│   └── schema/                     # generated JSON Schema (from engine Pydantic models)
├── validation/                     # CI-only accuracy harness (imports engine + drives vLLM)
│   ├── runner.py                   # launch vllm serve, capture reserved VRAM, compare to prediction
│   ├── matrix.yaml                 # GPU × model × quant × TP cases + pinned vLLM version
│   └── report.py                   # pass-rate report (published)
└── docker/
    ├── Dockerfile                  # backend (+ optional bundled static SPA) — one-container self-host
    └── docker-compose.yml          # local run convenience
```

### Architectural Boundaries
- **API boundary:** `POST /v1/calculate` + preset/meta endpoints; the *only* thing surfaces call. OpenAPI is the published contract.
- **Engine boundary:** pure package, no I/O, no framework imports; the sole owner of the calculation and of the shared Pydantic models. API/CLI/validation depend inward on it (dependency arrows point at the engine).
- **Preset boundary:** YAML files → validated by engine schema at load; presets are *data*, not code — contributing one requires no code change.
- **SPA boundary:** talks only to the API via the generated client; owns no calculation logic.
- **Validation boundary:** separate, CI-only, GPU-bound; imports the engine but never ships in the runtime image.

### Requirements-to-Structure Mapping
- **Config Input (FR1–FR5)** → `web/features/calculator/` (UI) + `engine/models.py` (input model) + `presets/`.
- **VRAM Calc & Fit (FR6–FR11)** → `engine/{weights,kv_cache,overhead,parallelism}.py`.
- **Serving Capacity (FR12–FR14)** → `engine/capacity.py`.
- **Remediation (FR15–FR16)** → `engine/remediation.py` + `web/features/calculator/`.
- **Command Generation (FR17–FR18)** → `engine/command.py`.
- **Transparency/Viz (FR19–FR22)** → `web/components/VramBar` + result flags in `engine/models.py`.
- **Multi-Surface Access (FR23–FR27)** → `web/`, `packages/api/`, `packages/cli/`, `docker/`.
- **Presets & Contribution (FR28–FR30)** → `presets/` + `api/presets_loader.py` + `ci.yml` validation.
- **Accuracy Validation (FR31–FR32)** → `validation/` + `validation-gpu.yml`.

### Data Flow
Inputs (SPA/CLI) → `POST /v1/calculate` → API validates (Pydantic) → **engine** computes in bytes → result object (breakdown, verdict, capacity, remediation, command, flags, vLLM version) → API serializes (snake_case) → surface formats to GiB at the edge. Presets load once at startup from YAML into memory.

### Development / Build / Deployment
- **Dev:** `uvicorn` for API (hot reload), `vite dev` for SPA (proxying `/v1` to the API), `typer` CLI run locally.
- **Build:** SPA → static bundle; backend → wheel(s); Docker image bundles backend (+ optional static SPA).
- **Deploy:** one container for self-host/air-gapped; public instance may split SPA (static host) from backend (container host). Config via env vars.

## Architecture Validation Results

### Coherence Validation ✅
**Decision Compatibility:** All choices cohere — Python 3.13 / FastAPI 0.139 / Typer 0.26 / Pydantic v2 share one ecosystem; React 19 + Vite 8 is a current, compatible SPA stack. No contradictions: stateless + no-DB + flat-file presets + no-auth reinforce each other and the air-gapped goal.
**Pattern Consistency:** The units rule, snake_case-on-the-wire, and engine-owned shared models all support the parity requirement (NFR3). Debounced-API-calls decision is consistent with "engine is the single source of truth."
**Structure Alignment:** The monorepo layout enforces the dependency direction (everything points inward at `packages/engine`); boundaries in the tree match the boundaries in the decisions.

### Requirements Coverage Validation ✅
**Functional Requirements:** All **32 FRs** mapped to concrete locations (see Requirements-to-Structure Mapping) — engine (FR6–FR17), surfaces (FR23–FR27), presets/contribution (FR28–FR30), validation (FR31–FR32), transparency (FR19–FR22).
**Non-Functional Requirements:** Accuracy (NFR1–4) → pure engine + golden tests + validation harness + result-flags; Performance (NFR5–7) → in-process math + static SPA + debounce; Portability (NFR8–10) → Docker/stateless; Security/Privacy (NFR11–13) → no-auth + no-logging + Pydantic validation + CI scanning; Maintainability (NFR14–16) → registries + flat-file presets + version pin; Accessibility (NFR17) → SVG viz + non-color-only encoding.

### Implementation Readiness Validation ✅
Decisions documented with pinned versions; patterns comprehensive with anti-patterns; structure complete and specific; the implementation sequence gives a clear build order.

### Gap Analysis Results
- **Critical gaps:** None.
- **Important gaps:** None blocking. One expected *calibration task* (not an architectural gap): the empirical constants in the overhead model (activation multiplier `k`, per-GPU fixed-context/NCCL values) are intentionally **to be calibrated by the validation harness** — the architecture assigns this to `validation/` rather than guessing values now. Correctly placed, flagged as first-real-data work.
- **Nice-to-have:** A dedicated UX spec would refine the SPA's interaction detail; not required for implementation to start.

### Architecture Completeness Checklist
**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment
**Overall Status:** **READY FOR IMPLEMENTATION** (all 16 checklist items confirmed; no critical gaps).
**Confidence Level:** **High** — the runtime is deliberately simple and the hard problem (calc correctness) is de-risked by `spec.txt` plus an early validation harness.
**Key Strengths:** engine-as-linchpin guarantees parity; boring/stable stack; simple stateless runtime; accuracy provable by construction (golden tests + GPU harness); extensible via registries + flat-file presets.
**Areas for Future Enhancement:** empirical overhead-constant calibration (harness); dedicated UX spec; the committed fast-follows (MLA math, shareable URLs, HF config.json ingest).

### Implementation Handoff
**AI Agent Guidelines:** follow decisions exactly; compute in bytes; import shared models from the engine; keep the engine I/O-free; preserve parity (no TS calc port); return results-with-flags, not exceptions, for over-provision.
**First Implementation Priority:** scaffold the monorepo (`create-vite` for `web`; uv/Poetry workspace for `packages/*`), then build `packages/engine` (models + `spec.txt` math) with its golden-test suite before any surface.
