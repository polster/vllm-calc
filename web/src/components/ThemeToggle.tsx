import { useState } from 'react'

import { effectiveTheme, toggleTheme, type Theme } from '../theme.ts'

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => effectiveTheme())

  return (
    <button
      type="button"
      onClick={() => setTheme(toggleTheme())}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
      className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm text-[var(--ink)] hover:border-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"
    >
      {theme === 'dark' ? '☀ Light' : '☾ Dark'}
    </button>
  )
}
