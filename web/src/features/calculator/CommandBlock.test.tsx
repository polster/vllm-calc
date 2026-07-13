import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { CommandBlock } from './CommandBlock.tsx'

const CMD =
  'vllm serve meta-llama/Llama-3.3-70B-Instruct --tensor-parallel-size 2 ' +
  '--quantization awq --max-model-len 8192 --gpu-memory-utilization 0.9'

afterEach(() => vi.restoreAllMocks())

describe('CommandBlock', () => {
  it('renders the full command text', () => {
    render(<CommandBlock command={CMD} />)
    expect(screen.getByText(/--tensor-parallel-size/)).toBeInTheDocument()
    // The full command is reconstructable from the code block.
    expect(screen.getByRole('figure').textContent).toContain(CMD)
  })

  it('copies to the clipboard and confirms with a toast + live announcement', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    render(<CommandBlock command={CMD} />)
    fireEvent.click(screen.getByRole('button', { name: 'Copy' }))

    await waitFor(() => expect(writeText).toHaveBeenCalledWith(CMD))
    expect(await screen.findByText('Copied ✓')).toBeInTheDocument()
    expect(screen.getByText('Command copied to clipboard')).toBeInTheDocument()
  })

  it('does not claim success when the Clipboard API is unavailable', async () => {
    vi.stubGlobal('navigator', {}) // no clipboard (insecure context / old browser)
    render(<CommandBlock command={CMD} />)
    fireEvent.click(screen.getByRole('button', { name: 'Copy' }))
    // Give any (incorrect) async success path a chance to run, then assert it didn't.
    await Promise.resolve()
    expect(screen.queryByText('Copied ✓')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Copy' })).toBeInTheDocument()
  })
})
