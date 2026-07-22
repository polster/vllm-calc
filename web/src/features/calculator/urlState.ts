import type { CalcInput } from '../../api/types.ts'
import { DEFAULT_INPUT, DEFAULT_SELECTION, type UiSelection } from './defaults.ts'

/** Encode/decode the full input scenario to/from URL query params, so a scenario
 *  survives refresh, back/forward, and copy-paste sharing (UX-DR8). The param
 *  shape is derived from DEFAULT_INPUT: unknown/malformed params fall back to the
 *  default rather than producing a broken input. */

export function encodeInput(input: CalcInput): string {
  const p = new URLSearchParams()
  for (const [key, value] of Object.entries(input)) {
    if (value === null || value === undefined) p.set(key, '')
    else p.set(key, typeof value === 'boolean' ? (value ? '1' : '0') : String(value))
  }
  return p.toString()
}

export function decodeInput(search: string): CalcInput {
  const p = new URLSearchParams(search)
  const out: Record<string, unknown> = { ...DEFAULT_INPUT }
  for (const [key, def] of Object.entries(DEFAULT_INPUT)) {
    if (!p.has(key)) continue
    const raw = p.get(key) ?? ''
    if (key === 'model_ref') {
      out[key] = raw === '' ? null : raw
    } else if (typeof def === 'number') {
      // Keep the default for blanks and non-finite garbage ('', ' ', 'Infinity').
      const n = Number(raw)
      if (raw.trim() !== '' && Number.isFinite(n)) out[key] = n
    } else if (typeof def === 'boolean') {
      out[key] = raw === '1'
    } else {
      out[key] = raw
    }
  }
  return out as unknown as CalcInput
}

/** Encode the full app state — the scenario plus the UI-only preset selection.
 *  The `model_preset`/`gpu_preset` params are additive (never sent to the API)
 *  and are omitted when empty to keep the placeholder state out of the URL. */
export function encodeState(input: CalcInput, selection: UiSelection): string {
  const p = new URLSearchParams(encodeInput(input))
  if (selection.modelPresetId) p.set('model_preset', selection.modelPresetId)
  if (selection.gpuPresetId) p.set('gpu_preset', selection.gpuPresetId)
  return p.toString()
}

/** Decode the scenario and the dropdown selection together. A bare query (no
 *  params at all — the fresh default load) restores DEFAULT_SELECTION so the
 *  dropdowns aren't blank; any query that carries params but lacks a preset
 *  param yields the empty placeholder rather than a wrong guess. */
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
