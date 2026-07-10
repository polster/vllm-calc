import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App.tsx'

describe('App shell', () => {
  it('renders the product name', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('vllm-calc')
  })

  it('renders both regions of the two-region layout', () => {
    render(<App />)
    expect(screen.getByTestId('inputs-region')).toBeInTheDocument()
    expect(screen.getByTestId('result-region')).toBeInTheDocument()
  })

  it('renders a theme toggle', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /theme/i })).toBeInTheDocument()
  })
})
