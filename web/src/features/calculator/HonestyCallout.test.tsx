import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Flag } from '../../api/types.ts'
import { HonestyCallout } from './HonestyCallout.tsx'

describe('HonestyCallout', () => {
  it('renders nothing without flags', () => {
    const { container } = render(<HonestyCallout flags={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('labels an over-provision estimate as conservative', () => {
    const flags: Flag[] = [{ type: 'over_provision_estimate', message: 'MLA over-provisions.' }]
    render(<HonestyCallout flags={flags} />)
    expect(screen.getByText('Conservative estimate')).toBeInTheDocument()
    expect(screen.getByText(/MLA over-provisions/)).toBeInTheDocument()
  })

  it('labels an unsupported architecture as not calibrated', () => {
    const flags: Flag[] = [{ type: 'unsupported', message: 'Not calibrated in v1.' }]
    render(<HonestyCallout flags={flags} />)
    expect(screen.getByText('Not calibrated')).toBeInTheDocument()
  })
})
