import type { CalcInput } from '../../api/types.ts'
import { DEFAULT_INPUT } from './defaults.ts'

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
      const n = Number(raw)
      if (!Number.isNaN(n)) out[key] = n // ignore garbage, keep the default
    } else if (typeof def === 'boolean') {
      out[key] = raw === '1'
    } else {
      out[key] = raw
    }
  }
  return out as unknown as CalcInput
}
