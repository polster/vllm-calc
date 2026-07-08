---
stepsCompleted: [1, 2, 3, 4, 5, 6]
status: 'complete'
overallReadiness: 'READY'
date: '2026-07-08'
project_name: 'vllm-calc'
documentsIncluded:
  - docs/prd.md
  - docs/architecture.md
  - docs/ux-design-specification.md
  - docs/epics.md
  - docs/product-brief-vllm-calc.md
  - docs/product-brief-vllm-calc-distillate.md
missingDocuments: []
---

# Implementation Readiness Assessment Report

**Date:** 2026-07-08
**Project:** vllm-calc

## Document Inventory

**PRD:** `docs/prd.md` (whole, complete) ✓
**Architecture:** `docs/architecture.md` (whole, status: complete) ✓
**UX Design:** `docs/ux-design-specification.md` (whole, status: complete) ✓ — plus `ux-design-directions.html`
**Epics & Stories:** `docs/epics.md` (whole, status: complete) ✓ — 4 epics, 22 stories
**Product Brief:** `docs/product-brief-vllm-calc.md` + distillate ✓ (supporting context)
**Brainstorming:** `docs/brainstorming/brainstorming-session-2026-07-01.md` ✓ (supporting context)

All four core planning documents present. No duplicate (whole + sharded) documents detected.

## PRD Analysis

### Functional Requirements
**32 FRs extracted** (full text in `docs/prd.md` § Functional Requirements and mirrored in `docs/epics.md` § Requirements Inventory), across 8 capability areas:
- Configuration Input: FR1–FR5
- VRAM Calculation & Fit: FR6–FR11
- Serving Capacity: FR12–FR14
- Remediation: FR15–FR16
- Command Generation: FR17–FR18
- Results Transparency & Visualization: FR19–FR22
- Multi-Surface Access: FR23–FR27
- Presets & Contribution: FR28–FR30
- Accuracy Validation: FR31–FR32

### Non-Functional Requirements
**17 NFRs extracted** across 6 categories: Accuracy & Correctness (NFR1–4 — the dominant driver: ±10% conservative accuracy, determinism, cross-surface parity, honest-failure), Performance (NFR5–7), Portability & Deployment (NFR8–10), Security & Privacy (NFR11–13), Maintainability & Extensibility (NFR14–16), Accessibility (NFR17 — WCAG 2.1 AA).

### Additional Requirements
From Architecture: greenfield monorepo scaffold, engine-as-shared-package (parity), REST `/v1` API + structured error contract, YAML flat-file presets, Docker deployment, two-tier CI (per-PR + GPU harness), bytes-only units invariant. From UX: 14 UX-DRs (design system, VerdictBanner, VramBreakdownBar, RemediationChips, CommandBlock, input surface, live loop, URL-state, inline validation, honesty callouts, default scenario, responsive layout, a11y baseline, theme toggle).

### PRD Completeness Assessment
PRD is complete and well-formed: every FR is testable and implementation-agnostic; NFRs are measurable (numeric targets on accuracy, latency, pass rate); scope is phased (MVP/Growth/Vision) with explicit deferrals (MLA/SWA exact math, pipeline parallelism). No ambiguous or unbounded requirements detected. Strong basis for traceability.

## Epic Coverage Validation

### Coverage Matrix (FR → Epic.Story)

| FR | Epic.Story | Status |
|----|-----------|--------|
| FR1 GPU preset/custom | 1.10 (input surface) | ✓ |
| FR2 model preset/custom | 1.10 | ✓ |
| FR3 quantization | 1.2 (weights), 1.10 | ✓ |
| FR4 ctx/concurrency/util/TP | 1.10 | ✓ |
| FR5 advanced levers | 2.3 | ✓ |
| FR6 3-term VRAM compute | 1.2, 1.3, 1.4 | ✓ |
| FR7 per-GPU TP sharding | 1.5 | ✓ |
| FR8 budget compare/verdict | 1.6 | ✓ |
| FR9 MoE total params | 1.2 | ✓ |
| FR10 parallelism validation | 1.5 | ✓ |
| FR11 KV-replication warning | 1.5 | ✓ |
| FR12 max concurrent | 1.6 | ✓ |
| FR13 capacity statement | 1.6 | ✓ |
| FR14 worst-case label | 1.6 | ✓ |
| FR15 remediation suggest | 2.2 | ✓ |
| FR16 apply suggestion | 2.2 | ✓ |
| FR17 command generation | 2.1 | ✓ |
| FR18 copy command | 2.1 | ✓ |
| FR19 breakdown viz | 1.11 | ✓ |
| FR20 expand overhead | 1.11 | ✓ |
| FR21 honest flags | 2.4 | ✓ |
| FR22 vLLM version label | 1.6, 1.11 | ✓ |
| FR23 SPA surface | 1.9–1.11 | ✓ |
| FR24 HTTP API surface | 1.8 | ✓ |
| FR25 CLI surface | 3.1 | ✓ |
| FR26 local Docker backend | 3.2 | ✓ |
| FR27 cross-surface parity | 1.8 (engine-owned), 3.1 | ✓ |
| FR28 add preset | 4.1, 4.2 | ✓ |
| FR29 validate presets (CI) | 4.1 | ✓ |
| FR30 preset provenance | 4.1 | ✓ |
| FR31 validation harness | 4.3 | ✓ |
| FR32 CI pass rate | 4.4 | ✓ |

### Missing Requirements
**None.** No PRD FR is uncovered. No orphan FRs (FRs in epics but not the PRD) detected. All 14 UX-DRs also trace to stories (1.9–1.11, 2.1–2.5).

### Coverage Statistics
- Total PRD FRs: **32**
- FRs covered in epics: **32**
- Coverage percentage: **100%**
- UX-DR coverage: 14/14 (100%) · NFRs addressed across stories + NFR-specific stories (4.3/4.4 for accuracy)

## UX Alignment Assessment

### UX Document Status
**Found** — `docs/ux-design-specification.md` (complete) + `docs/ux-design-directions.html`.

### UX ↔ PRD Alignment
- **Journeys align:** UX Journeys A/B/C map directly to PRD Journeys 1 (happy path), 2 (no-go + remediation), 4 (custom model); PRD Journey 3 (CLI/CI) correctly treated as a non-screen flow.
- **Core value preserved:** UX centers the verdict + capacity sentence (FR8/12/13), remediation (FR15/16), command (FR17/18), transparency/expand (FR19/20), and honest flags (FR21) — all PRD FRs.
- **Accessibility:** UX operationalizes NFR17 (WCAG 2.1 AA, non-color-only status, ARIA-live verdict) with concrete mechanisms.
- No UX requirement contradicts the PRD.

### UX ↔ Architecture Alignment
- **Supported end-to-end:** the debounced-API-call decision (architecture) directly enables the UX live-recompute loop within NFR5/NFR6 latency; React+Vite + Tailwind/Radix (chosen in UX) is consistent with the architecture's "SPA framework deferred to design phase" note; the two custom components map to `web/components` in the architecture tree.
- **Parity intact:** UX puts no calculation in the client — consistent with the architecture's single-engine parity invariant (NFR3).
- No UI need is unsupported by the architecture.

### Alignment Notes (benign)
- **URL-as-state scope:** the PRD listed shareable URLs as a *Growth* fast-follow, but UX + epics place basic URL-state in v1 (Story 2.5). This is a deliberate, low-cost pull-forward that also enables the future shareable-scenario feature — noted as an intentional scope refinement, not a conflict.
- **Default pre-computed scenario + light/dark themes** are UX-additive (not in the PRD text) and fully consistent with PRD goals; no rework implied.

### Warnings
None. UX is present, complete, and coherent with both PRD and Architecture.

## Epic Quality Review

### Best-Practices Compliance
| Check | Epic 1 | Epic 2 | Epic 3 | Epic 4 |
|-------|--------|--------|--------|--------|
| Delivers user value | ✓ (with note) | ✓ | ✓ | ✓ |
| Independent (no need for a *later* epic) | ✓ | ✓ | ✓ | ✓ |
| Stories sized for one dev session | ✓ | ✓ | ✓ | ✓ |
| No forward dependencies | ✓ (with note) | ✓ | ✓ | ✓ |
| Entities/data created only when needed | ✓ (no DB; presets in 1.7) | ✓ | ✓ | ✓ |
| Clear Given/When/Then ACs | ✓ | ✓ | ✓ | ✓ |
| FR traceability maintained | ✓ | ✓ | ✓ | ✓ |

### 🔴 Critical Violations
**None.** No technical-milestone epics, no epic requiring a future epic, no epic-sized unimplementable stories. Starter-template setup is correctly Story 1.1 (matches Architecture). Greenfield setup (scaffold + CI) is early.

### 🟠 Major Issues
**None.**

### 🟡 Minor Concerns (non-blocking, with remediation)
1. **Epic 1 contains engine/API "building-block" stories (1.2–1.8) with no *standalone user-facing* value.** This is inherent to a calculation-engine product (the engine *is* the value) and is acceptable because they live within one epic that delivers end-to-end value, are strictly sequenced, and each ships golden/unit tests. *Remediation: none required — but keep them inside Epic 1 (do not split into a technical "engine" epic, which would be the real anti-pattern).*
2. **Story 1.10 ↔ 1.11 result-render boundary.** Story 1.10 (input surface + live recompute) implies results appear on screen, but the result *components* (`VerdictBanner`, `VramBreakdownBar`) are built in 1.11 — a mild ordering ambiguity. *Remediation: 1.10 should render a minimal inline result (e.g. raw verdict text + numbers) so it is independently completable; 1.11 then upgrades that to the designed hero components. Alternatively, swap so the bar/banner land before the live-loop wiring. Low effort; clarify in the story text before dev picks it up.*
3. **`vllm serve` command sits in Epic 2, not Epic 1.** Deliberate (Epic 1 = "know," Epic 2 = "act"), and defensible since a fit verdict is standalone value — but note Epic 1 alone ships *without* a copyable command. *Remediation: none required; confirmed intentional in the epic-design step.*

### Remediation Summary
No blocking issues. One worth a one-line story edit before implementation (concern #2); the other two are documented-and-accepted design choices, not defects.

## Summary and Recommendations

### Overall Readiness Status
**READY** (for implementation).

All four core planning artifacts are present, complete, and mutually aligned. FR coverage is 100% (32/32) with full UX-DR coverage (14/14) and no orphan requirements. No critical or major quality violations. The three minor concerns are non-blocking (two are documented design choices; one is a one-line story clarification).

### Critical Issues Requiring Immediate Action
**None.** There are no blockers to starting implementation.

### Recommended Next Steps
1. **(Optional, 1-minute edit)** Clarify Story 1.10 so it renders a minimal inline result, with Story 1.11 upgrading to the `VerdictBanner` / `VramBreakdownBar` components — removes the only ordering ambiguity.
2. **Begin implementation at Story 1.1** (scaffold the monorepo + CI skeleton), then build the engine (Stories 1.2–1.6) **with its golden-value tests first** — the accuracy moat is established here.
3. **Stand up the validation-harness plumbing early** (even before full calibration) so overhead constants can be tuned against real `vllm serve` data as the engine matures (Epic 4 informs Epic 1's constants).
4. Keep the engine as the single source of truth (no calc logic in SPA/CLI) to preserve the parity invariant (NFR3) throughout.

### Final Note
This assessment identified **3 minor concerns across 1 category** (epic quality) and **zero critical or major issues**. The planning chain (brief → PRD → architecture → UX → epics) is complete, traceable, and internally consistent. You may proceed to implementation as-is; addressing concern #2 first is a trivial, recommended polish.

**Assessor:** Implementation-readiness review (facilitated 2026-07-08). **Status: READY.**
