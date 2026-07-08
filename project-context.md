# Project context (rules for AI agents)

Load this before working in the repo. It is the short, binding rule set; the full
reasoning lives in `docs/architecture.md`, `docs/prd.md`, and `docs/ux-design-specification.md`.

## What this is
vllm-calc: a VRAM calculator answering "will this OSS LLM fit on my GPUs under vLLM?"
Full-stack, greenfield. One calculation engine reached by three surfaces (SPA, CLI, API).

## Architecture invariants (do not violate)
- **Engine = single source of truth.** `packages/engine` is pure, I/O-free, deterministic,
  and owns the shared Pydantic models. API/CLI/validation import it. No calc logic in the SPA.
- **Bytes only in the engine.** Convert to GiB at edges. (A ~7% GiB/GB slip is a correctness bug.)
- **Conservative accuracy is a hard invariant.** A "fits" verdict must never OOM: predictions
  bias to over-predict; target ±10% vs. real `vllm serve` reserve (validated in Epic 4).
- **Per-GPU TP math:** weights & KV divide by TP; KV divisor is `min(TP, kv_heads)` (replication
  wall); overhead is paid per GPU. Validate TP divides heads and equals GPU count.
- **Honest failure:** flag over-provision (MLA/sliding-window) / unsupported as result flags,
  not confident-wrong numbers or thrown errors.
- **snake_case on the API wire; versioned `/v1`.** OpenAPI is the contract for the SPA client.
- **No DB, no auth (v1). Presets are version-controlled YAML.** Stateless backend, Docker-runnable.

## Stack
Python 3.13+ (engine/api/cli), FastAPI + Pydantic v2, Typer (CLI), React 19 + Vite 7 + TS
(SPA, Tailwind + Radix/shadcn design system, dark-default). Tooling: **uv** workspace
(Python, `uv.lock`) + **npm** (web; divergence from architecture's pnpm — see CONTRIBUTING.md).

## Build order (epics)
E1 Know the Answer (scaffold → engine → API → SPA) · E2 Act (command, remediation) ·
E3 Reach (CLI, Docker) · E4 Prove (validation harness, preset contribution).
Engine stories ship **golden-tests-first**.
