import { describe, expect, it } from 'vitest'

import { DEFAULT_INPUT, DEFAULT_SELECTION } from './defaults.ts'
import { decodeInput, decodeState, encodeInput, encodeState } from './urlState.ts'

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

  it('falls back to the default for empty and non-finite numbers', () => {
    expect(decodeInput('ctx_len=').ctx_len).toBe(DEFAULT_INPUT.ctx_len)
    expect(decodeInput('total_params=Infinity').total_params).toBe(DEFAULT_INPUT.total_params)
  })

  it('decodes an empty model_ref as null (custom model)', () => {
    expect(decodeInput('model_ref=').model_ref).toBeNull()
  })

  it('decodes booleans from 1/0', () => {
    expect(decodeInput('enforce_eager=1').enforce_eager).toBe(true)
    expect(decodeInput('enforce_eager=0').enforce_eager).toBe(false)
  })

  it('round-trips the scenario together with the preset selection', () => {
    const input = { ...DEFAULT_INPUT, ctx_len: 4096 }
    const selection = { modelPresetId: 'qwen2.5-7b', gpuPresetId: 'h100-80gb' }
    expect(decodeState(encodeState(input, selection))).toEqual({ input, selection })
  })

  it('restores the default selection for an empty query', () => {
    expect(decodeState('')).toEqual({ input: DEFAULT_INPUT, selection: DEFAULT_SELECTION })
  })

  it('yields empty selection when a scenario has params but no preset ids', () => {
    expect(decodeState('ctx_len=4096').selection).toEqual({ modelPresetId: '', gpuPresetId: '' })
  })

  it('round-trips a custom model selection', () => {
    const selection = { modelPresetId: 'custom', gpuPresetId: '' }
    const encoded = encodeState(DEFAULT_INPUT, selection)
    expect(encoded).toContain('model_preset=custom')
    expect(encoded).not.toContain('gpu_preset')
    expect(decodeState(encoded).selection).toEqual(selection)
  })
})
