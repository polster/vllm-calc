import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { GpuPreset, ModelPreset } from '../../api/types.ts'
import { DEFAULT_INPUT, type UiSelection } from './defaults.ts'
import { InputPanel } from './InputPanel.tsx'

function gpu(id: string, name: string, vram_gib: number): GpuPreset {
  return { id, name, vram_gib, source: 'hf', last_verified: '2026-07-10', vllm_version_checked: '0.13' }
}

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
  source: 'https://huggingface.co/Qwen/Qwen2.5-7B',
  last_verified: '2026-07-10',
  vllm_version_checked: '0.13',
}

const NO_SELECTION: UiSelection = { modelPresetId: '', gpuPresetId: '' }

function renderPanel(props: {
  selection?: UiSelection
  setInput?: (patch: unknown) => void
  setSelection?: (patch: Partial<UiSelection>) => void
  modelPresets?: ModelPreset[]
  gpuPresets?: GpuPreset[]
}) {
  return render(
    <InputPanel
      input={DEFAULT_INPUT}
      setInput={props.setInput ?? vi.fn()}
      selection={props.selection ?? NO_SELECTION}
      setSelection={props.setSelection ?? vi.fn()}
      modelPresets={props.modelPresets ?? []}
      gpuPresets={props.gpuPresets ?? []}
    />,
  )
}

describe('InputPanel', () => {
  it('autofills architecture fields and records the selection when a preset is chosen', () => {
    const setInput = vi.fn()
    const setSelection = vi.fn()
    renderPanel({ setInput, setSelection, modelPresets: [QWEN] })

    fireEvent.change(screen.getByLabelText('Model preset'), { target: { value: 'qwen2.5-7b' } })

    expect(setSelection).toHaveBeenCalledWith({ modelPresetId: 'qwen2.5-7b' })
    expect(setInput).toHaveBeenCalledWith(
      expect.objectContaining({ layers: 28, kv_heads: 4, hidden_size: 3584 }),
    )
  })

  // The dropdown value now lives in app state, so the purpose caption is driven
  // by the `selection` prop (this is what makes it show on a seeded/shared load).
  it("shows the selected model's purpose when a preset is selected", () => {
    renderPanel({ selection: { modelPresetId: 'qwen2.5-7b', gpuPresetId: '' }, modelPresets: [QWEN] })
    expect(screen.getByText(QWEN.purpose!)).toBeInTheDocument()
  })

  it('hides the purpose for a custom model', () => {
    renderPanel({ selection: { modelPresetId: 'custom', gpuPresetId: '' }, modelPresets: [QWEN] })
    expect(screen.queryByText(QWEN.purpose!)).not.toBeInTheDocument()
  })

  it('hides the purpose when no preset is selected', () => {
    renderPanel({ selection: NO_SELECTION, modelPresets: [QWEN] })
    expect(screen.queryByText(QWEN.purpose!)).not.toBeInTheDocument()
  })

  it('falls back to the placeholder when the selected id is not in the list (loading/stale)', () => {
    // e.g. presets not fetched yet, or a shared link naming a removed preset.
    renderPanel({ selection: { modelPresetId: 'llama-3.3-70b', gpuPresetId: '' }, modelPresets: [] })
    expect((screen.getByLabelText('Model preset') as HTMLSelectElement).value).toBe('')
    // and it must not claim the architecture came from a preset
    expect(screen.queryByText(/architecture from preset/)).not.toBeInTheDocument()
  })

  it('reflects a GPU preset even when another preset shares its VRAM', () => {
    // 80 GiB matches both A100 and H100 — identity is stored, never inferred.
    renderPanel({
      selection: { modelPresetId: '', gpuPresetId: 'h100-80gb' },
      gpuPresets: [gpu('a100-80gb', 'NVIDIA A100 80GB', 80), gpu('h100-80gb', 'NVIDIA H100 80GB', 80)],
    })
    expect((screen.getByLabelText('GPU preset') as HTMLSelectElement).value).toBe('h100-80gb')
  })

  it('edits a workload field through setInput', () => {
    const setInput = vi.fn()
    renderPanel({ setInput })
    fireEvent.change(screen.getByLabelText('Context length'), { target: { value: '4096' } })
    expect(setInput).toHaveBeenCalledWith({ ctx_len: 4096 })
  })

  it('toggles the enforce_eager advanced lever', () => {
    const setInput = vi.fn()
    renderPanel({ setInput })
    fireEvent.click(screen.getByRole('checkbox'))
    expect(setInput).toHaveBeenCalledWith({ enforce_eager: true })
  })

  it('renders an accessible info tooltip trigger per field', () => {
    renderPanel({})
    // Representative triggers across a number field, a select, and the checkbox lever.
    expect(screen.getByRole('button', { name: 'About Context length' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'About Quantization' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'About enforce_eager' })).toBeInTheDocument()
  })

  it('keeps each input’s accessible name equal to its label', () => {
    renderPanel({})
    // The tooltip trigger must not pollute the control's accessible name.
    expect(screen.getByLabelText('Context length').tagName).toBe('INPUT')
    expect(screen.getByLabelText('Quantization').tagName).toBe('SELECT')
  })
})
