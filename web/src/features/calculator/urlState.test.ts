import { describe, expect, it } from 'vitest'

import { DEFAULT_INPUT } from './defaults.ts'
import { decodeInput, encodeInput } from './urlState.ts'

describe('urlState', () => {
  it('round-trips a modified scenario', () => {
    const input = { ...DEFAULT_INPUT, ctx_len: 4096, enforce_eager: true, kv_dtype: 'fp8' as const }
    expect(decodeInput(encodeInput(input))).toEqual(input)
  })

  it('returns the default scenario for an empty query', () => {
    expect(decodeInput('')).toEqual(DEFAULT_INPUT)
  })

  it('falls back to the default for a malformed number', () => {
    expect(decodeInput('ctx_len=notanumber').ctx_len).toBe(DEFAULT_INPUT.ctx_len)
  })

  it('decodes an empty model_ref as null (custom model)', () => {
    expect(decodeInput('model_ref=').model_ref).toBeNull()
  })

  it('decodes booleans from 1/0', () => {
    expect(decodeInput('enforce_eager=1').enforce_eager).toBe(true)
    expect(decodeInput('enforce_eager=0').enforce_eager).toBe(false)
  })
})
