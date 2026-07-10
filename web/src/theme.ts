/** Light/dark theme management: persisted to localStorage, applied via the
 *  `data-theme` attribute on <html> (which overrides the system preference). */

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'vllm-calc-theme'

function systemPrefersDark(): boolean {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

export function getStoredTheme(): Theme | null {
  const value = localStorage.getItem(STORAGE_KEY)
  return value === 'light' || value === 'dark' ? value : null
}

/** The theme currently in effect: an explicit stored choice, else the system. */
export function effectiveTheme(): Theme {
  return getStoredTheme() ?? (systemPrefersDark() ? 'dark' : 'light')
}

export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
}

/** On load: honor a stored choice; otherwise leave it to the CSS media query. */
export function initTheme(): void {
  const stored = getStoredTheme()
  if (stored) applyTheme(stored)
}

/** Flip the effective theme, persist it, apply it, and return the new value. */
export function toggleTheme(): Theme {
  const next: Theme = effectiveTheme() === 'dark' ? 'light' : 'dark'
  localStorage.setItem(STORAGE_KEY, next)
  applyTheme(next)
  return next
}
