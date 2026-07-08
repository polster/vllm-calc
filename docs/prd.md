---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments:
  - docs/product-brief-vllm-calc.md
  - docs/product-brief-vllm-calc-distillate.md
  - spec.txt
  - docs/brainstorming/brainstorming-session-2026-07-01.md
workflowType: 'prd'
releaseMode: phased
classification:
  projectType: 'Full-stack web app (SPA front-end + backend API owning the calculation engine & preset store, distributable as a local Docker container) + companion CLI (thin client of the same API)'
  domain: 'Developer tools / ML-infrastructure tooling'
  complexity: 'medium-high'
  projectContext: 'greenfield'
---

# Product Requirements Document - vllm-calc

**Author:** Simon
**Date:** 2026-07-06

## Executive Summary

**vllm-calc** is an open-source tool that answers the question every engineer faces before serving an open-source LLM with vLLM: *"Will this fit on my GPUs?"* Users specify a GPU, model, quantization, context length, concurrency, and tensor-parallel size; vllm-calc computes the per-GPU VRAM breakdown (weights + KV cache + overhead) against the usable budget, returns a plain-language go/no-go verdict with serving capacity, suggests the nearest fitting configuration on a no-go, and generates the ready-to-run `vllm serve` command. It ships as three surfaces over one calculation engine: a browser SPA, a companion CLI, and a backend API — the latter runnable locally (Docker) for self-hosted or air-gapped use.

The problem it solves is a costly trial-and-error loop: today, engineers discover whether a configuration fits by launching it and waiting for an out-of-memory crash, then guessing at `--gpu-memory-utilization`, context length, or GPU count and retrying — each cycle burning minutes and GPU budget. vLLM has no pre-flight sizing tool, and existing web calculators target single-GPU llama.cpp/GGUF hobbyists, model inference overhead as a flat "+20%" fudge, and either ignore tensor parallelism or scale it naively. The primary user is the **multi-GPU serving engineer** deploying 70B/MoE models across 2–8 GPUs — where the pain is sharpest and hand-calculation hardest.

### What Makes This Special

**Provable accuracy is the moat.** vllm-calc models what vLLM *actually* reserves at startup — a transparent three-term overhead (fixed CUDA context + activations + CUDA graphs) instead of a percentage fudge, real per-GPU tensor-parallel sharding with a warning at the KV-replication wall (`TP > num_kv_heads`), and GQA-aware KV cache — all calibrated against real `vllm serve` runs to a ±10% target, biased conservative so a "fits" verdict never OOMs. The core insight: VRAM-fit is not one number but `weights + KV + overhead` competing for `gpu_util × per-GPU VRAM`, and the errors that bite people are exactly the ones incumbents get wrong. Command generation alone is table stakes (a competitor already does it); the differentiator is being the tool that's *correct* — and that, on a no-go, tells you *how to make it fit*. The differentiation moment: a user sees "❌ won't fit at 128k — fits at 90k, or at FP8," copies the generated command, and it works on the first launch.

## Project Classification

- **Project Type:** Full-stack web app — SPA front-end + backend API that owns the calculation engine and preset store (distributable as a local Docker container, hosted or self-run) + companion CLI as a thin client of the same API.
- **Domain:** Developer tools / ML-infrastructure tooling.
- **Complexity:** Medium–High — architecture surface (backend, CLI, API versioning, validation harness) atop a high-complexity calculation domain that is largely de-risked in the existing `spec.txt`.
- **Project Context:** Greenfield.

## Success Criteria

### User Success
- A serving engineer configures a multi-GPU deployment **once**, the verdict says "fits," and `vllm serve` launches **without OOM on the first try** — the trial-and-error loop is eliminated.
- On a no-go, the user reaches a working config **without a single failed launch**, using the nearest-fitting-config suggestion.
- The generated `vllm serve` command runs **as-is** (no manual flag correction needed) for the modeled configuration.
- "Aha" moment: the user trusts the number enough to provision hardware / commit a config **based on the tool alone**, not a test launch.

### Business Success (OSS adoption)
- **3-month:** validated baseline of the top ~15–20 models live; referenced in ≥2 vLLM/HF community threads; first external preset contributions merged.
- **12-month:** recognized as a go-to vLLM pre-flight tool — sustained repeat usage, a healthy cadence of community-contributed presets, inbound links from vLLM/HF ecosystem docs or discussions.
- GitHub stars/forks tracked as a **coarse** signal only — not the goal.

### Technical Success
- **Accuracy:** predicted VRAM within **±10%** of actual `vllm serve` startup reserve across the validation suite, **biased to over-predict** (predicted ≥ actual) so a "fits" verdict does not OOM under the stated assumptions.
- **Validation harness** exists, is CI-run against a pinned vLLM version range, and its pass rate is published.
- Calculation parity across all three surfaces (SPA, CLI, API) — identical inputs yield identical results (single backend engine guarantees this).
- Backend runs locally via Docker with no external dependencies (air-gapped-capable).

### Measurable Outcomes
- Validation-suite pass rate **published and green** (≥90% of cases within ±10%, 0 under-predictions on "fits" cases).
- Time-to-answer: a user goes from inputs → verdict + command in **under a minute**, no install for the web path.
- Opt-in "did it fit?" post-launch feedback trends positive.

## Product Scope

_This section states the feature tiers at a glance; the later "Project Scoping & Phased Development" section expands each phase with strategy, must-have breakdown, and risk mitigation._

### MVP - Minimum Viable Product
Core memory model (weights + GQA-aware KV + 3-term overhead); per-GPU **tensor parallelism** + KV-replication warning; **nearest-fitting-config** remediation; curated & validated presets (top ~15–20 models + common GPUs) + user-added custom presets; VRAM visualization + capacity verdict sentence; **`vllm serve` command generation**; quantization affecting weights & KV; MoE total-parameter handling; **backend API + Docker** + **companion CLI**; **validation harness** with ±10% accuracy target.

### Growth Features (Post-MVP)
Exact **MLA** KV math (DeepSeek) — fast-follow #1; **URL-encoded shareable scenarios**; **HF `config.json` auto-ingest** for custom models; sliding-window (Mistral/Gemma) exact KV; richer CLI (CI-gate mode).

### Vision (Future)
Pipeline parallelism & multi-node; throughput/latency modeling; cloud-cost ($/instance-SKU) layer; speculative decoding & chunked-prefill precision; embeddable widget for model cards / vLLM docs; the default automated pre-flight gate in deployment pipelines.

## User Journeys

**Journey 1 — Primary user, happy path (web SPA): Deepa sizes a 70B deployment.**
Deepa, an ML platform engineer, has two A100 80GBs and needs to serve Llama-3.3-70B at 32k context for ~30 concurrent users. Today she'd launch, watch it OOM, and start guessing. Instead she opens vllm-calc, picks the A100 GPU preset (count 2), the Llama-3.3-70B model preset, AWQ 4-bit, 32k context, 32 concurrent, TP=2. The breakdown bar renders instantly: weights/KV/overhead per GPU against the 0.9×80GB budget, verdict **"✅ Fits — supports up to 41 concurrent."** She expands the overhead term to sanity-check it against her mental model, copies the generated `vllm serve …` command, runs it — and it comes up clean on the first try. *Reveals: input controls, preset selection, per-GPU breakdown viz, capacity verdict, expandable overhead, command generation.*

**Journey 2 — Primary user, no-go + remediation: the config that doesn't fit.**
Same Deepa, but she wants 128k context. Verdict: **"❌ Won't fit — needs ~104GB/GPU, budget is 72GB."** Instead of leaving her stuck, vllm-calc surfaces the nearest fitting configs: *"Fits at 90k context · or with FP8 KV cache · or at TP=4 (4 GPUs)."* She picks FP8 KV, re-checks, gets a green verdict and command — **without a single failed launch.** *Reveals: no-go verdict with reason, nearest-fitting-config remediation engine, one-click apply of a suggestion.*

**Journey 3 — API/CI consumer (CLI): Marco gates a deployment pipeline.**
Marco maintains the team's model-serving CI. He adds `vllm-calc check --model llama-3.3-70b --gpu a100-80gb:2 --tp 2 --ctx 32k --max-seqs 32` as a pre-deploy step against their **self-hosted Docker backend** (no config leaves the network). If a model/config change won't fit, the CLI exits non-zero and fails the build *before* a GPU is ever touched. *Reveals: CLI thin-client over the API, local/Docker backend, machine-readable output + exit codes, calc parity with the web UI.*

**Journey 4 — Community preset contributor: Aisha adds a new model.**
Aisha wants to size a freshly released model that isn't in the presets yet. She enters its architecture params as a **custom model** (layers, kv_heads, head_dim, hidden_size, total params, MoE flag) and gets her answer immediately. Finding it accurate, she opens a PR contributing the preset; CI validates the preset's schema and (ideally) checks it against the model's published config before merge, so the curated set grows without silent rot. *Reveals: custom-preset entry form, preset schema, contribution + validation path.*

### Journey Requirements Summary
These journeys collectively require: **(a)** an input surface with GPU/model presets + custom entry; **(b)** the calculation engine (weights + GQA KV + 3-term overhead + per-GPU TP) exposed via API; **(c)** per-GPU VRAM visualization + plain-language capacity verdict; **(d)** a nearest-fitting-config remediation engine; **(e)** `vllm serve` command generation; **(f)** a CLI thin-client with exit codes and a locally-runnable Docker backend; **(g)** a preset store with custom entry and a contribution/validation workflow.

## Domain-Specific Requirements

### Accuracy & vLLM Version Coupling
- The calculation models vLLM's *actual* runtime behavior, which **drifts across vLLM versions** (overhead, CUDA-graph capture, MLA execution paths, defaults like `gpu_memory_utilization` and `max_num_seqs`). Requirement: the engine declares a **supported/pinned vLLM version range**, and the validation harness runs against it. Results are labeled with the version they're calibrated for.
- The conservative bias (predicted ≥ actual on "fits") is a **hard product invariant**, not a nice-to-have — an under-prediction that OOMs breaks the core trust promise. Known failure modes (driver/fragmentation, coexisting GPU processes, non-default vLLM flags) are documented in-product.

### Data Handling & Self-Hosting
- Inputs are non-sensitive (GPU specs, model architecture params) — **no PII/regulated data**. But model choice and cluster shape can be commercially sensitive; enterprises must be able to run **fully locally** (Docker backend, air-gapped) so **no configuration data leaves their network**. The public hosted instance must not require accounts or log identifying request content beyond anonymous/opt-in usage signals.

### Preset Integrity (domain anti-pattern: silent rot)
- Stale or wrong presets are **worse than none** — they silently feed the accuracy-critical engine bad numbers and erode trust. Requirement: presets are **schema-validated in CI**, ideally checked against the model's published `config.json`, and carry provenance (source + last-verified). Curated baseline is authoritative; community contributions are gated by validation.

### Ecosystem-Change Resilience
- The OSS model landscape moves weekly (new architectures like MLA, new quant formats like FP8, longer contexts). The model schema and KV formula must be **extensible without core rewrites**, and the tool must **fail honestly** (flag "over-provisioned estimate" / "unsupported architecture") rather than silently return a wrong-but-confident number.

## Innovation & Novel Patterns

### Detected Innovation Areas
- **Validated accuracy as a product feature.** Existing calculators assert accuracy; vllm-calc *proves* it via a CI validation harness comparing predictions to real `vllm serve` startup reserve, publishing the pass rate. Accuracy becomes a legible, testable artifact rather than a claim — novel in this tool category.
- **Faithful mechanism modeling over heuristics.** Replacing the industry-standard flat "+20%" with a transparent three-term overhead, real per-GPU TP sharding, and the KV-replication-wall behavior — modeling *what vLLM actually does* rather than approximating it.
- **Remediation, not just verdict.** The "nearest fitting config" engine inverts the tool from a passive answer ("no") into an active advisor ("no, but fits at 90k / FP8 / TP=4"), directly attacking the guess-and-retry loop.
- **One engine, three surfaces, self-hostable.** A single backend calculation core reached by SPA, CLI, and API — locally runnable (Docker/air-gapped) — guaranteeing parity and enabling CI-gated pre-flight checks.

### Market Context & Competitive Landscape
No incumbent occupies the intersection: `llmvramcalculator` is accurate (GQA/MLA) but generates no command and treats TP naively; `WireUnwired` generates a command but omits TP/GQA and uses outdated syntax; HF accelerate ignores KV entirely. vLLM itself has no pre-flight tool (documented unmet demand, issue #22291). The defensible wedge is **vLLM-accurate + validated + remediating + command-generating**.

### Validation Approach
Build the validation harness *early* (MVP), not last: a matrix of real GPU × model × quant × TP configs launched under a pinned vLLM version, comparing predicted vs. actually-reserved VRAM, gating merges in CI. This both *is* the accuracy proof and *is* the calibration mechanism for the overhead constants.

### Risk Mitigation
- **Risk: accuracy claim fails to hold.** Mitigation → conservative bias invariant + published pass rate + honest "over-provisioned estimate / unsupported" flags. Fallback: narrow the supported model/GPU matrix to what's validated rather than over-promising.
- **Risk: vLLM version drift silently degrades accuracy.** Mitigation → pinned version range + harness re-run on vLLM bumps.

## Full-Stack Web App Specific Requirements

### Project-Type Overview
vllm-calc is a full-stack developer tool: a **FastAPI (Python) backend** owning the calculation engine and preset store, a **browser SPA** front-end, and a **companion CLI** — all three sharing one engine via the backend API. Python is chosen so the engine, CLI, and the vLLM-launching validation harness live in one ecosystem and can parse model `config.json` natively. Presets are **version-controlled flat files (JSON/YAML)** in the repo.

### Technical Architecture Considerations
- **Calculation engine (backend-owned):** pure functions implementing the `spec.txt` v1 model (weights + GQA KV + 3-term overhead + per-GPU TP + capacity + remediation). No per-surface duplication — SPA and CLI both call the API, guaranteeing parity.
- **Deployment:** backend packaged as a **Docker image**, runnable hosted or fully locally/air-gapped with no external dependencies at runtime. SPA is static-hostable and points at a configurable API base URL (public or local).
- **Frontend:** SPA framework choice deferred to the architecture phase; requirement is a fast, no-install, single-page experience with live-updating VRAM visualization.

### API Design
- **Endpoints (indicative):** `POST /calculate` (inputs → breakdown + verdict + capacity + remediation + generated command); `GET /presets/models` & `GET /presets/gpus` (list curated + validate custom); `GET /health`/`GET /version` (reports engine + supported vLLM version range). Stateless; JSON in/out.
- **Auth:** **none** for v1 — no accounts, no login. Public instance takes no identifying data; optional anonymous usage telemetry only.
- **Contract stability:** versioned API (e.g. `/v1/…`) since the CLI is an independent client; response schema is the single source of truth for all surfaces.

### CLI Design
- Thin client over the API (points at a configurable/local backend). Core command `vllm-calc check …` returns a human-readable verdict and **exits non-zero on no-go** for CI gating; a `--json` flag emits machine-readable output.

### Preset Store & Contribution
- Flat JSON/YAML files per model/GPU with a defined schema; **CI schema-validation** on PRs, ideally cross-checked against the model's published `config.json`; provenance (source + last-verified) tracked via file fields + git history. Custom presets entered at runtime are validated against the same schema without requiring a contribution.

### Implementation Considerations
- **Validation harness** is a first-class MVP deliverable (Python, launches real `vllm serve`, compares predicted vs. reserved VRAM, CI-gated against a pinned vLLM version range).
- Engine must be **extensible** (new attention types / quant formats) without core rewrites; unsupported inputs **fail honestly** with a flag rather than a confident wrong number.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy
**MVP Approach: problem-solving MVP** — the smallest thing that makes the primary user (multi-GPU serving engineer) say *"this replaced my launch-and-crash loop."* The bar for "useful" is a **trustworthy** fit verdict for a curated set of real models, not breadth. Accuracy-first, not feature-first: a narrow-but-validated tool beats a broad-but-unproven one, because the entire moat is trust.
**Resource assumption:** small OSS team / solo maintainer; scope sized so the validated model matrix, not the UI, is the pacing item.

### MVP Feature Set (Phase 1)
**Core journeys supported:** Journey 1 (happy-path web sizing), Journey 2 (no-go + remediation), Journey 3 (CLI/CI gating), Journey 4 (custom-preset entry + contribution).
**Must-have capabilities:**
- Calculation engine: weights + GQA-aware KV + 3-term overhead + per-GPU TP (+ KV-replication warning), per `spec.txt`.
- Capacity verdict sentence + per-GPU VRAM visualization (expandable overhead).
- Nearest-fitting-config remediation.
- `vllm serve` command generation.
- Quantization (weights + KV); MoE total-param handling.
- Curated & validated presets (top ~15–20 models + common GPUs) + runtime custom presets; flat-file store + CI schema validation.
- FastAPI backend + Docker (locally runnable) + SPA + companion CLI (exit codes, `--json`).
- **Validation harness** with the ±10% conservative-accuracy target, CI-gated against a pinned vLLM version.

### Post-MVP Features
**Phase 2 (Growth):** exact MLA KV math (DeepSeek) — fast-follow #1; URL-encoded shareable scenarios; HF `config.json` auto-ingest; sliding-window (Mistral/Gemma) exact KV; richer CLI CI-gate ergonomics.
**Phase 3 (Vision/Expansion):** pipeline parallelism & multi-node; throughput/latency modeling; cloud-cost ($/instance-SKU) layer; speculative decoding & chunked-prefill precision; embeddable widget for model cards / vLLM docs.

### Risk Mitigation Strategy
- **Technical (accuracy is the whole game):** the overhead constants + conservative bias are only credible if measured → validation harness is MVP, not deferred. Fallback: **narrow the supported matrix to what's validated** rather than over-promising breadth.
- **Market (a competitor already generates commands):** differentiate on *provable* accuracy + remediation; make the validated pass-rate visible so the moat is legible at decision time.
- **Resource (solo/small team):** MVP is deliberately narrow-and-correct; community preset contributions (gated by CI) extend coverage without core team effort. If resources shrink, cut *model breadth*, never accuracy/validation.

## Functional Requirements

### Configuration Input
- FR1: A user can select a GPU from a curated preset (model, VRAM, count) or define a custom GPU (VRAM per GPU, count).
- FR2: A user can select a model from a curated preset or define a custom model by its architecture parameters (total params, layers, kv_heads, head_dim, hidden_size, MoE flag).
- FR3: A user can specify a quantization scheme that affects both weights and KV cache (e.g. FP16, FP8, AWQ/GPTQ 4-bit).
- FR4: A user can specify context length, desired concurrency (max_seqs), gpu_memory_utilization, and tensor-parallel size.
- FR5: A user can adjust advanced levers that affect overhead (e.g. `max_num_batched_tokens`, `enforce_eager`).

### VRAM Calculation & Fit Assessment
- FR6: The system can compute per-GPU VRAM as weights + GQA-aware KV cache + a three-term overhead (fixed context + activations + CUDA graphs).
- FR7: The system can apply tensor-parallel sharding per GPU, dividing weights and KV while replicating overhead across GPUs.
- FR8: The system can compare required VRAM against the usable budget (`gpu_memory_utilization × per-GPU VRAM`) and return a go/no-go verdict.
- FR9: The system can compute MoE model weights from total (not active) parameters.
- FR10: The system can validate parallelism constraints (TP divides attention-heads and KV-heads; TP equals GPU count) and reject invalid configurations with a reason.
- FR11: The system can warn when TP exceeds the model's KV-head count (KV-replication wall), indicating KV will not shard further.

### Serving Capacity
- FR12: The system can compute maximum concurrent sequences supported (bounded by the KV budget and the batch cap).
- FR13: The system can express the verdict as a capacity statement comparing requested vs. supported concurrency (e.g. "asked 32; supports 47").
- FR14: The system can label capacity results as conservative/worst-case (full-context-per-sequence assumption).

### Remediation
- FR15: On a no-go, the system can suggest one or more nearest fitting configurations (e.g. reduced context, different quantization, higher TP / more GPUs).
- FR16: A user can apply a suggested configuration and recompute.

### Command Generation
- FR17: The system can generate a runnable `vllm serve` command whose flags match the computed configuration (model, TP, quantization, KV-cache dtype, max-model-len, gpu-memory-utilization, etc.).
- FR18: A user can copy the generated command.

### Results Transparency & Visualization
- FR19: A user can view a per-GPU VRAM breakdown visualization (weights / KV / overhead vs. usable budget).
- FR20: A user can expand the overhead figure into its three component terms.
- FR21: The system can flag when an estimate is a known over-provision (MLA / sliding-window models) or the model architecture is unsupported, rather than returning a silently-wrong number.
- FR22: The system can report the vLLM version range the result is calibrated for.

### Multi-Surface Access
- FR23: A user can perform a calculation through a browser SPA.
- FR24: A developer can perform a calculation through the HTTP API.
- FR25: A developer can perform a calculation through the CLI, which returns machine-readable output (`--json`) and exits non-zero on a no-go for CI gating.
- FR26: An operator can run the backend locally (Docker) with no external runtime dependencies, so no configuration data leaves their network.
- FR27: All surfaces return identical results for identical inputs (single shared engine).

### Presets & Contribution
- FR28: A contributor can add a model or GPU preset as a version-controlled file conforming to a defined schema.
- FR29: The system can validate preset files against the schema (in CI), ideally cross-checking a model preset against its published `config.json`.
- FR30: A preset carries provenance (source and last-verified information).

### Accuracy Validation
- FR31: The system can be validated by a harness that launches real `vllm serve` configurations and compares predicted vs. actually-reserved VRAM.
- FR32: The validation harness can run in CI against a pinned vLLM version range and report its pass rate.

## Non-Functional Requirements

### Accuracy & Correctness (primary quality attribute)
- NFR1: Predicted VRAM must land within **±10%** of actual `vllm serve` startup reserve across the validation suite, and must be **biased to over-predict** (predicted ≥ actual) on any "fits" verdict — an under-prediction that OOMs is a correctness failure.
- NFR2: Validation-suite pass rate must be **≥90%** within ±10% with **zero under-predictions** on "fits" cases, published and CI-gated against a pinned vLLM version range.
- NFR3: The calculation must be **deterministic** — identical inputs always yield identical outputs — and **identical across all surfaces** (SPA, CLI, API).
- NFR4: When inputs fall outside validated coverage (e.g. MLA/sliding-window/unsupported architecture), the system must return a labeled/flagged result rather than an unflagged wrong number.

### Performance
- NFR5: A calculation (inputs → verdict + breakdown + remediation + command) must return in **under 500 ms** server-side for a single request.
- NFR6: The web path must require **no installation** and reach an interactive state in **under 3 seconds** on a typical broadband connection; input changes update the visualization near-instantly.
- NFR7: End-to-end user time-to-answer (open → verdict + command) is **under one minute**.

### Portability & Deployment
- NFR8: The backend must run as a **self-contained Docker image** with **no external runtime dependencies** or network calls required for the core calculation (air-gapped-capable).
- NFR9: The SPA must be **static-hostable** and configurable to target any API base URL (public or local).
- NFR10: A single backend instance must comfortably serve typical single-team/community concurrent load; being stateless, it scales horizontally behind a load balancer if needed.

### Security & Privacy
- NFR11: v1 requires **no authentication** and stores **no user accounts**.
- NFR12: The public hosted instance must **not persist or log identifying request content** beyond anonymous, opt-in aggregate usage signals; self-hosted deployments keep all data on-network by construction.
- NFR13: Standard web hardening applies (input validation on API, no execution of user-supplied content, dependency-vulnerability scanning in CI).

### Maintainability & Extensibility
- NFR14: The calculation engine must be **extensible to new attention types and quantization formats** without rewriting the core (new cases are additive).
- NFR15: Presets are **version-controlled flat files** with a schema-validated contribution path; adding coverage requires no code change.
- NFR16: Results and the engine must declare the **vLLM version range** they target, so version drift is explicit and re-calibration is traceable.

### Accessibility
- NFR17: The SPA should meet **WCAG 2.1 AA** basics — keyboard navigability, sufficient contrast, and non-color-only encoding of the fit/no-fit state (since the verdict is red/green).
