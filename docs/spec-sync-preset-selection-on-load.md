---
title: 'Reflect the loaded/shared preset selection in the input pane'
type: 'bugfix'
created: '2026-07-22'
status: 'done'
baseline_commit: '3d674ebf02af9a8982939d2af0dc7c6427ddc85a'
context: ['{project-root}/project-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On load the app always has a full scenario (from the URL, or `DEFAULT_INPUT` = Llama-3.3-70B on A100 80GB), yet the Model/GPU **Preset** dropdowns show "— choose … —". They are bound to local `useState` in `InputPanel` that is never seeded from the actual `input`, so the selection the config came from is invisible and does not survive refresh/back-forward/share.

**Approach:** Make the selected preset ids part of the shareable app state. Persist `model_preset`/`gpu_preset` (UI-only params) in the URL alongside the scenario, seed them on load (empty URL → the default scenario's presets), restore them on back/forward, and drive the dropdowns from that state instead of disconnected local state. This reflects the selection for both dropdowns with no ambiguity — GPU cannot be recovered from `gpu_vram_gib` alone (80 GiB matches both A100 and H100), so its identity must be stored, not inferred.

## Boundaries & Constraints

**Always:**
- Keep the "no blank state" default: an empty URL shows Llama-3.3-70B + A100 80GB, and the dropdowns now show those presets.
- Keep `model_ref` as the source of the `vllm serve` command; the new `model_preset` param is UI-only and is never sent to the engine/API.
- `DEFAULT_SELECTION` must stay consistent with `DEFAULT_INPUT` (documented next to it).
- An explicit user pick is always preserved verbatim — selecting a GPU whose VRAM equals another preset's must keep the chosen one, not snap away.

**Ask First:**
- Any change to `CalcInput`, the engine wire contract, or the `/v1` API shape. (This fix must not touch them — selection params are UI-only.)

**Never:**
- Do not remove the default scenario or introduce a blank-input start state (that was explicitly decided against).
- Do not infer GPU identity from `gpu_vram_gib`.
- Do not add engine/API fields for the selection.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fresh load, empty query | `''` | selection = `DEFAULT_SELECTION` (llama-3.3-70b + a100-80gb); both dropdowns show them | N/A |
| Shared link | `?...&model_preset=qwen2.5-7b&gpu_preset=h100-80gb` | dropdowns show Qwen2.5 7B + H100 80GB | absent preset param → placeholder `''` |
| Custom model chosen | selection `modelPresetId='custom'` | dropdown shows "Custom…"; `model_ref` cleared to null; URL has `model_preset=custom` | N/A |
| Pick GPU sharing VRAM | select H100 80GB (vram 80, also A100) | dropdown stays "H100 80GB"; VRAM field = 80; URL `gpu_preset=h100-80gb` | N/A |
| Back/forward | popstate to prior URL | input **and** selection restored together | malformed params fall back per existing `decodeInput` |

</frozen-after-approval>

## Code Map

- `web/src/features/calculator/defaults.ts` -- add `DEFAULT_SELECTION` (+ `UiSelection` shape if placed here); keep it beside `DEFAULT_INPUT`.
- `web/src/features/calculator/urlState.ts` -- add `encodeState(input, selection)` / `decodeState(search)`; keep `encodeInput`/`decodeInput` as the scenario core.
- `web/src/features/calculator/useCalculator.ts` -- own `selection` state; seed via `decodeState`, restore on popstate, sync to URL (same debounced effect), expose `selection` + `setSelection`.
- `web/src/features/calculator/InputPanel.tsx` -- replace local `modelId`/`gpuId` `useState` with `selection`/`setSelection` props; derive `fromPreset`/`selectedPurpose` from `selection.modelPresetId`.
- `web/src/features/calculator/CalculatorPage.tsx` -- thread `selection`/`setSelection` from the hook into `InputPanel`.
- `*.test.ts(x)` for urlState, useCalculator, InputPanel -- update/extend (see below).

## Tasks & Acceptance

**Execution:**
- [x] `web/src/features/calculator/defaults.ts` -- add `export interface UiSelection { modelPresetId: string; gpuPresetId: string }` and `export const DEFAULT_SELECTION: UiSelection = { modelPresetId: 'llama-3.3-70b', gpuPresetId: 'a100-80gb' }` with a comment tying it to `DEFAULT_INPUT`.
- [x] `web/src/features/calculator/urlState.ts` -- `encodeState` appends `model_preset`/`gpu_preset` only when non-empty; `decodeState(search)` returns `{ input: decodeInput(search), selection }` where absent preset params → `DEFAULT_SELECTION` **iff the query has no keys**, else `''`.
- [x] `web/src/features/calculator/useCalculator.ts` -- add `selection` state seeded from `decodeState`; extend the popstate handler and the debounced URL-sync effect (use `encodeState`, add `selection` to deps); add `setSelection(patch: Partial<UiSelection>)`; return `selection`, `setSelection`.
- [x] `web/src/features/calculator/InputPanel.tsx` -- accept `selection`/`setSelection` props; `selectModel`/`selectGpu` call `setSelection({...})` then the existing `setInput(...)`; the two `<select value>` bind to `selection.*`; `fromPreset`/`selectedPurpose` derive from `selection.modelPresetId`.
- [x] `web/src/features/calculator/CalculatorPage.tsx` -- pass `selection`/`setSelection` through.
- [x] `web/src/features/calculator/urlState.test.ts` -- add `encodeState`↔`decodeState` round-trip (incl. custom + shared-link), empty-query → `DEFAULT_SELECTION`, and params-present-without-preset → `''`.
- [x] `web/src/features/calculator/useCalculator.test.ts` -- add: default selection on empty URL; seed selection from URL; `setSelection` reflected in `window.location.search`.
- [x] `web/src/features/calculator/InputPanel.test.tsx` -- pass `selection`/`setSelection`; split the purpose test into (a) onChange fires `setSelection`+`setInput`, (b) purpose/"architecture from preset" render is driven by the `selection` prop (present → shown, `'custom'`/`''` → hidden). Fix the `QWEN` fixture `source` to a `huggingface.co` URL.

**Acceptance Criteria:**
- Given an empty URL, when the app loads, then the Model dropdown shows "Llama 3.3 70B" and the GPU dropdown shows "NVIDIA A100 80GB".
- Given a link with `model_preset`/`gpu_preset`, when the app loads, then both dropdowns show those presets and the scenario fields match.
- Given any dropdown selection or field edit, when it settles, then the URL carries the current `model_preset`/`gpu_preset` and is copy-shareable.
- Given back/forward navigation, when popstate fires, then dropdowns and fields both restore to that URL's state.
- Given `make check-web`, when run, then lint, typecheck, tests, and build all pass.

## Design Notes

Selection is UI-only state living next to the scenario in the URL — `model_ref` (engine-facing, drives the command) is unchanged; `model_preset`/`gpu_preset` (UI-facing, drive the dropdowns) are additive. `decodeState` distinguishing "empty query" (→ defaults) from "query present but preset param missing" (→ `''` placeholder) is what makes both the fresh-load default and externally-truncated links behave sanely; every URL the app emits includes the params.

```ts
export function decodeState(search: string): { input: CalcInput; selection: UiSelection } {
  const p = new URLSearchParams(search)
  const bare = [...p.keys()].length === 0
  return {
    input: decodeInput(search),
    selection: {
      modelPresetId: p.get('model_preset') ?? (bare ? DEFAULT_SELECTION.modelPresetId : ''),
      gpuPresetId: p.get('gpu_preset') ?? (bare ? DEFAULT_SELECTION.gpuPresetId : ''),
    },
  }
}
```

## Verification

**Commands:**
- `make check-web` -- expected: eslint, `tsc --noEmit`, `vitest run`, and `vite build` all succeed.

**Manual checks:**
- `cd web && npm run dev`, open `/`: Model shows "Llama 3.3 70B", GPU shows "NVIDIA A100 80GB". Pick H100 80GB → stays selected, VRAM=80, URL gains `gpu_preset=h100-80gb`. Copy URL into a new tab → same selection restored. Browser Back → previous selection restored.

## Suggested Review Order

**The state model (start here)**

- Selection is UI-only state — the shape that decouples the dropdown from `model_ref`.
  [`defaults.ts:38`](../web/src/features/calculator/defaults.ts#L38)

- The core round-trip: bare query → default selection; params-but-no-preset → placeholder.
  [`urlState.ts:53`](../web/src/features/calculator/urlState.ts#L53)

- Additive, UI-only URL params — never reach the engine/API.
  [`urlState.ts:42`](../web/src/features/calculator/urlState.ts#L42)

**Wiring it into the hook**

- Seed input + selection once from the URL (lazy initializer).
  [`useCalculator.ts:37`](../web/src/features/calculator/useCalculator.ts#L37)

- Restore both on back/forward, and sync both to the URL in a dedicated debounced effect.
  [`useCalculator.ts:61`](../web/src/features/calculator/useCalculator.ts#L61)

**UI binding (highest-risk stop)**

- Clamp the `<select>` value to a rendered option so a loading/stale id degrades to the placeholder, not blank.
  [`InputPanel.tsx:85`](../web/src/features/calculator/InputPanel.tsx#L85)

- Record the pick in selection, then apply the preset's fields as before.
  [`InputPanel.tsx:100`](../web/src/features/calculator/InputPanel.tsx#L100)

- Thread selection/setSelection through the page.
  [`CalculatorPage.tsx:21`](../web/src/features/calculator/CalculatorPage.tsx#L21)

**Tests (supporting)**

- urlState round-trips, default, and placeholder cases.
  [`urlState.test.ts:34`](../web/src/features/calculator/urlState.test.ts#L34)

- Hook: default selection, URL seed, URL sync, popstate restore.
  [`useCalculator.test.ts:107`](../web/src/features/calculator/useCalculator.test.ts#L107)

- Panel: purpose caption, placeholder fallback, VRAM-sharing GPU stays selected.
  [`InputPanel.test.tsx:66`](../web/src/features/calculator/InputPanel.test.tsx#L66)
