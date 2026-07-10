import { afterEach, describe, expect, it } from 'vitest'

import { applyTheme, effectiveTheme, getStoredTheme, initTheme, toggleTheme } from './theme.ts'

afterEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

describe('theme', () => {
  it('applyTheme sets the data-theme attribute', () => {
    applyTheme('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('toggleTheme flips, persists, and applies', () => {
    // jsdom has no matchMedia → effective defaults to light; first toggle → dark.
    const next = toggleTheme()
    expect(next).toBe('dark')
    expect(getStoredTheme()).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(effectiveTheme()).toBe('dark')

    expect(toggleTheme()).toBe('light')
    expect(getStoredTheme()).toBe('light')
  })

  it('initTheme applies a stored choice', () => {
    localStorage.setItem('vllm-calc-theme', 'dark')
    initTheme()
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('initTheme leaves no attribute when nothing is stored', () => {
    initTheme()
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false)
  })
})
