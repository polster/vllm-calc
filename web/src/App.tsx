// App shell (Story 1.9) + calculator (Story 1.10): header with theme toggle,
// then the two-region calculator page.

import { ThemeToggle } from './components/ThemeToggle.tsx'
import { CalculatorPage } from './features/calculator/CalculatorPage.tsx'

export default function App() {
  return (
    <div className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
        <h1 className="text-lg font-bold tracking-tight">
          vllm<span className="text-[var(--accent)]">-calc</span>
        </h1>
        <ThemeToggle />
      </header>
      <CalculatorPage />
    </div>
  )
}
