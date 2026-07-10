import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { ModelPreset } from '../../api/types.ts'
import { DEFAULT_INPUT } from './defaults.ts'
import { InputPanel } from './InputPanel.tsx'

const QWEN: ModelPreset = {
  id: 'qwen2.5-7b',
  name: 'Qwen2.5 7B',
  total_params: 7_610_000_000,
  layers: 28,
  attention_heads: 28,
  kv_heads: 4,
  head_dim: 128,
  hidden_size: 3584,
  is_moe: false,
  attention_type: 'standard',
  source: 'hf',
  last_verified: '2026-07-10',
}

describe('InputPanel', () => {
  it('autofills architecture fields when a model preset is chosen', () => {
    const setInput = vi.fn()
    render(
      <InputPanel input={DEFAULT_INPUT} setInput={setInput} modelPresets={[QWEN]} gpuPresets={[]} />,
    )
    fireEvent.change(screen.getByLabelText('Model preset'), { target: { value: 'qwen2.5-7b' } })
    expect(setInput).toHaveBeenCalledWith(
      expect.objectContaining({ layers: 28, kv_heads: 4, hidden_size: 3584 }),
    )
  })

  it('edits a workload field through setInput', () => {
    const setInput = vi.fn()
    render(
      <InputPanel input={DEFAULT_INPUT} setInput={setInput} modelPresets={[]} gpuPresets={[]} />,
    )
    fireEvent.change(screen.getByLabelText('Context length'), { target: { value: '4096' } })
    expect(setInput).toHaveBeenCalledWith({ ctx_len: 4096 })
  })

  it('toggles the enforce_eager advanced lever', () => {
    const setInput = vi.fn()
    render(
      <InputPanel input={DEFAULT_INPUT} setInput={setInput} modelPresets={[]} gpuPresets={[]} />,
    )
    fireEvent.click(screen.getByRole('checkbox'))
    expect(setInput).toHaveBeenCalledWith({ enforce_eager: true })
  })
})
