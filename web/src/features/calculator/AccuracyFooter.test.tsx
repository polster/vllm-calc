import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ValidationStatus } from '../../api/types.ts'
import { AccuracyFooter } from './AccuracyFooter.tsx'

describe('AccuracyFooter', () => {
  it('shows the measured pass rate and calibrated range once validated', async () => {
    const status: ValidationStatus = {
      status: 'validated',
      calibrated_vllm_range: '>=0.13,<0.14',
      pass_rate: 0.95,
      gate_passed: true,
    }
    render(<AccuracyFooter fetch={() => Promise.resolve(status)} />)
    expect(await screen.findByText(/95% of cases within ±10%/)).toBeInTheDocument()
    expect(screen.getByText(/calibrated for vLLM >=0.13,<0.14/)).toBeInTheDocument()
  })

  it('states it is not yet validated when pending', async () => {
    const status: ValidationStatus = {
      status: 'pending',
      calibrated_vllm_range: '>=0.13,<0.14',
    }
    render(<AccuracyFooter fetch={() => Promise.resolve(status)} />)
    expect(await screen.findByText(/not yet validated against real vLLM/)).toBeInTheDocument()
  })
})
