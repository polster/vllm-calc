import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { ModelPreset } from '../../api/types.ts'
import { DEFAULT_INPUT } from './defaults.ts'
import { InputPanel } from './InputPanel.tsx'

const QWEN: ModelPreset = {
  id: 'qwen2.5-7b',
  name: 'Qwen2.5 7B',
  purpose: 'Capable small model for coding and math',
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
  vllm_version_checked: '0.13',
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

  it("shows the selected model's purpose, and hides it for a custom model", () => {
    const setInput = vi.fn()
    render(
      <InputPanel input={DEFAULT_INPUT} setInput={setInput} modelPresets={[QWEN]} gpuPresets={[]} />,
    )
    // Nothing selected yet → no purpose caption.
    expect(screen.queryByText(QWEN.purpose!)).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Model preset'), { target: { value: 'qwen2.5-7b' } })
    expect(screen.getByText(QWEN.purpose!)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Model preset'), { target: { value: 'custom' } })
    expect(screen.queryByText(QWEN.purpose!)).not.toBeInTheDocument()
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

  it('renders an accessible info tooltip trigger per field', () => {
    render(
      <InputPanel input={DEFAULT_INPUT} setInput={vi.fn()} modelPresets={[]} gpuPresets={[]} />,
    )
    // Representative triggers across a number field, a select, and the checkbox lever.
    expect(screen.getByRole('button', { name: 'About Context length' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'About Quantization' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'About enforce_eager' })).toBeInTheDocument()
  })

  it('keeps each input’s accessible name equal to its label', () => {
    render(
      <InputPanel input={DEFAULT_INPUT} setInput={vi.fn()} modelPresets={[]} gpuPresets={[]} />,
    )
    // The tooltip trigger must not pollute the control's accessible name.
    expect(screen.getByLabelText('Context length').tagName).toBe('INPUT')
    expect(screen.getByLabelText('Quantization').tagName).toBe('SELECT')
  })
})
