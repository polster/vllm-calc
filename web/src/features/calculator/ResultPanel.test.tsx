import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { axe } from 'vitest-axe'

import type { CalcResult } from '../../api/types.ts'
import { ResultPanel } from './ResultPanel.tsx'
import { VerdictBanner } from './VerdictBanner.tsx'
import { VramBreakdownBar } from './VramBreakdownBar.tsx'

const GIB = 1024 ** 3

function makeResult(fits: boolean): CalcResult {
  return {
    fits,
    requested_max_seqs: 32,
    max_concurrent: fits ? 42 : 12,
    verdict: fits ? 'Fits — supports up to 42 (you asked for 32).' : "Won't fit — supports up to 12.",
    worst_case_note: 'Conservative: assumes every sequence uses the full context.',
    supported_vllm_range: '>=0.13,<0.14',
    warnings: [],
    serve_command:
      'vllm serve meta-llama/Llama-3.3-70B-Instruct --tensor-parallel-size 2 --quantization awq --max-model-len 8192 --gpu-memory-utilization 0.9',
    breakdown: {
      weights_per_gpu_bytes: 17 * GIB,
      kv_per_gpu_bytes: 24 * GIB,
      overhead_fixed_context_bytes: 1 * GIB,
      overhead_activations_bytes: GIB / 2,
      overhead_cuda_graphs_bytes: 1 * GIB,
      overhead_total_bytes: Math.round(2.5 * GIB),
      used_per_gpu_bytes: Math.round(43.5 * GIB),
      budget_per_gpu_bytes: 72 * GIB,
      available_for_kv_bytes: Math.round(52 * GIB),
    },
  }
}

describe('VerdictBanner', () => {
  it('shows a fit verdict with icon + text in a live region (not color-only)', () => {
    const { container } = render(<VerdictBanner result={makeResult(true)} />)
    expect(screen.getByText('Fits')).toBeInTheDocument()
    expect(screen.getByText(/supports up to 42/)).toBeInTheDocument()
    expect(container.querySelector('[aria-live="polite"]')).not.toBeNull()
  })

  it('shows a no-go verdict', () => {
    render(<VerdictBanner result={makeResult(false)} />)
    expect(screen.getByText("Won't fit")).toBeInTheDocument()
  })
})

describe('VramBreakdownBar', () => {
  it('exposes an image role with a descriptive label and a screen-reader table', () => {
    render(<VramBreakdownBar breakdown={makeResult(true).breakdown} />)
    const img = screen.getByRole('img')
    expect(img.getAttribute('aria-label')).toMatch(/weights .* KV cache .* overhead/i)
    // SR table alternative includes the budget row
    expect(screen.getByRole('rowheader', { name: 'Budget' })).toBeInTheDocument()
  })

  it('can expand the overhead into its three sub-terms', () => {
    render(<VramBreakdownBar breakdown={makeResult(true).breakdown} />)
    expect(screen.getByText('Show overhead breakdown')).toBeInTheDocument()
    expect(screen.getByText('Activations')).toBeInTheDocument()
    expect(screen.getByText('CUDA graphs')).toBeInTheDocument()
  })
})

describe('ResultPanel a11y', () => {
  it('has no axe violations for a computed result', async () => {
    const { container } = render(
      <ResultPanel result={makeResult(true)} status="ready" error={null} />,
    )
    const results = await axe(container)
    expect(results.violations).toEqual([])
  })

  it('keeps the last result visible while showing an error', () => {
    render(<ResultPanel result={makeResult(true)} status="error" error="TP invalid" />)
    expect(screen.getByRole('alert')).toHaveTextContent('TP invalid')
    expect(screen.getByText('Fits')).toBeInTheDocument()
  })
})
