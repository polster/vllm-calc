---
title: 'Input-field tooltips in the calculator InputPanel'
type: 'feature'
created: '2026-07-22'
status: 'done'
baseline_commit: 'efc47bf00f1879b09820bfd368a3d9ee1668aba5'
context:
  - '{project-root}/project-context.md'
  - '{project-root}/spec.txt'
  - '{project-root}/docs/ux-design-specification.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The `InputPanel` exposes ~17 parameters (params, layers, KV heads, TP, gpu_memory_utilization, max_num_batched_tokens…) with only terse labels. New users cannot tell what to configure or why a value matters, so the calculator's "will it fit?" answer is hard to trust or act on.

**Approach:** Add a small, accessible info-tooltip next to every input field's label, showing a short plain-language description sourced from `spec.txt`'s parameter definitions. Use the project's designated Radix (shadcn/ui) design system — the first component to pull Radix in, as anticipated in Story 1.9.

## Boundaries & Constraints

**Always:**
- Tooltip copy is grounded in `spec.txt` (KEY INPUTS + formula notes) — no invented behavior.
- Keyboard- and screen-reader-accessible: each trigger is a real `<button type="button">` with an `aria-label`; tooltip content is exposed via Radix's ARIA wiring. Existing `vitest-axe` smoke stays at 0 violations.
- Preserve every input's current accessible name so existing tests keep passing — inputs get an explicit `aria-label` equal to their visible label (selects already have one).
- Theme-aware styling via existing CSS tokens (`--surface-2`, `--border`, `--muted`, `--accent`); works in dark (default) and light.
- Tooltip descriptions live in ONE map, so copy is edited in a single place.

**Ask First:**
- Any change to the calculation, API wire shape, or preset data (this is presentational only).
- Adding any dependency beyond `@radix-ui/react-tooltip`.

**Never:**
- No new calc logic in the SPA; no engine/API/CLI changes.
- Don't rely on the native `title` attribute (poor a11y, no styling, no keyboard/touch story).
- Don't change field ordering, grouping, defaults, or the Advanced disclosure behavior.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Hover trigger | Pointer over a field's info button | Tooltip with that field's description appears | N/A |
| Keyboard focus | Tab to the info button, no mouse | Same tooltip appears; Esc dismisses | N/A |
| Screen reader | AT reads the input | Input's accessible name unchanged; trigger announced as "About <field>" | N/A |
| Field with no mapped help | (guard) field key missing from map | No trigger rendered for that field | No crash |

</frozen-after-approval>

## Code Map

- `web/src/features/calculator/InputPanel.tsx` -- the fields to annotate; `NumberField` + `<select>` labels get a trigger; wrap tree in `Tooltip.Provider`
- `web/src/features/calculator/fieldHelp.ts` -- NEW: `Record<string,string>` of field-key → description, copy sourced from `spec.txt`
- `web/src/features/calculator/FieldTooltip.tsx` -- NEW: Radix tooltip trigger (info button) + portalled content, token-styled
- `web/src/features/calculator/InputPanel.test.tsx` -- assert triggers exist per field; keep existing 3 tests green
- `web/package.json` -- add `@radix-ui/react-tooltip` runtime dependency
- `spec.txt` (KEY INPUTS, formula notes) -- source of the descriptions

## Tasks & Acceptance

**Execution:**
- [x] `web/package.json` -- add `@radix-ui/react-tooltip` to `dependencies`; run `npm install` in `web/`
- [x] `web/src/features/calculator/fieldHelp.ts` -- export `FIELD_HELP` map keyed by field id (`total_params`, `layers`, `attention_heads`, `kv_heads`, `head_dim`, `hidden_size`, `weight_quant`, `gpu_vram_gib`, `gpu_count`, `tensor_parallel_size`, `ctx_len`, `max_seqs`, `gpu_memory_utilization`, `kv_dtype`, `max_num_batched_tokens`, `max_num_seqs_cap`, `enforce_eager`); one concise sentence each, grounded in `spec.txt`
- [x] `web/src/features/calculator/FieldTooltip.tsx` -- `FieldTooltip({ label, description })`: `Tooltip.Root` → `Tooltip.Trigger asChild` wrapping `<button type="button" aria-label={\`About ${label}\`}>` with an `aria-hidden` info glyph → portalled `Tooltip.Content` (+ arrow), styled with CSS tokens
- [x] `web/src/features/calculator/InputPanel.tsx` -- threaded a `help` prop through `NumberField` (+ `FieldLabel` helper); render `FieldTooltip` in each label row; gave each `<input>` an explicit `aria-label`; added tooltips to all four `<select>` labels + the two preset pickers and the `enforce_eager` checkbox; wrapped the panel body in `<Tooltip.Provider delayDuration={200}>`
- [x] `web/src/features/calculator/InputPanel.test.tsx` -- added two tests: representative triggers render (`About Context length` / `About Quantization` / `About enforce_eager`) and inputs' accessible names are unchanged; existing 3 tests still pass

**Acceptance Criteria:**
- Given the calculator is open, when I hover or keyboard-focus any field's info button, then a readable description for that specific field appears and dismisses on blur/Esc.
- Given a screen reader, when it reaches a field, then the input's accessible name is exactly its label (existing `getByLabelText` queries still resolve) and the info trigger is announced separately.
- Given the full web suite, when I run lint + typecheck + tests + build, then all gates pass and `vitest-axe` reports 0 violations.

## Design Notes

Accessible-name trap: inputs are currently wrapped by `<label>`, so nesting a button inside would pollute the input's computed name and break `getByLabelText('Context length')`. Fix by giving each input an explicit `aria-label` (wins over wrapping-label text) and placing the trigger as a non-label sibling in the label row. Radix triggers on hover AND focus for free, giving keyboard support without extra code. Single `Tooltip.Provider` at the panel root shares timing config.

## Verification

**Commands:**
- `cd web && npm run lint` -- expected: clean
- `cd web && npm run typecheck` -- expected: no TS errors
- `cd web && npm test` -- expected: all suites pass incl. axe smoke (0 violations)
- `cd web && npm run build` -- expected: production build succeeds

**Manual checks:**
- `npm run dev`, hover and tab through fields: each shows its description; readable in dark and light theme.

## Suggested Review Order

**Copy source (the "what")**

- Central help-text map for the 17 calc fields — grounded in `spec.txt`.
  [`fieldHelp.ts:9`](../web/src/features/calculator/fieldHelp.ts#L9)
- Preset-picker copy kept in the same file (single source of truth).
  [`fieldHelp.ts:54`](../web/src/features/calculator/fieldHelp.ts#L54)

**Tooltip primitive (accessibility core)**

- Trigger is a real focusable button; opens on hover AND keyboard focus.
  [`FieldTooltip.tsx:13`](../web/src/features/calculator/FieldTooltip.tsx#L13)
- Portalled, token-styled content — theme-aware in light/dark.
  [`FieldTooltip.tsx:23`](../web/src/features/calculator/FieldTooltip.tsx#L23)

**Wiring into the panel**

- `FieldLabel` pairs a real `<label htmlFor>` with a sibling tooltip — restores click-to-focus without polluting the accessible name.
  [`InputPanel.tsx:30`](../web/src/features/calculator/InputPanel.tsx#L30)
- `NumberField` generates a stable id per field via `useId`.
  [`InputPanel.tsx:46`](../web/src/features/calculator/InputPanel.tsx#L46)
- Single `Tooltip.Provider` at the panel root shares open-delay config.
  [`InputPanel.tsx:111`](../web/src/features/calculator/InputPanel.tsx#L111)
- Model-preset select keeps `aria-label` (visible "Preset" ≠ accessible name).
  [`InputPanel.tsx:118`](../web/src/features/calculator/InputPanel.tsx#L118)

**Tests (peripheral)**

- Triggers render per field; input accessible names unchanged.
  [`InputPanel.test.tsx:54`](../web/src/features/calculator/InputPanel.test.tsx#L54)
