import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { Remediation } from '../../api/types.ts'
import { RemediationChips } from './RemediationChips.tsx'

const REMS: Remediation[] = [
  { label: 'FP8 KV cache', detail: 'fits — up to 45 concurrent', delta: { kv_dtype: 'fp8' } },
  { label: 'Context ≤ 32k', detail: 'fits — up to 40 concurrent', delta: { ctx_len: 32768 } },
]

describe('RemediationChips', () => {
  it('renders nothing when there are no remediations', () => {
    const { container } = render(<RemediationChips remediations={[]} onApply={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a chip per remediation', () => {
    render(<RemediationChips remediations={REMS} onApply={() => {}} />)
    expect(screen.getByRole('button', { name: 'FP8 KV cache' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Context ≤ 32k' })).toBeInTheDocument()
  })

  it('applies the exact delta when a chip is clicked', () => {
    const onApply = vi.fn()
    render(<RemediationChips remediations={REMS} onApply={onApply} />)
    fireEvent.click(screen.getByRole('button', { name: 'FP8 KV cache' }))
    expect(onApply).toHaveBeenCalledWith({ kv_dtype: 'fp8' })
  })
})
