// App shell (Story 1.9): the responsive two-region layout — inputs and the
// living result. Inputs (Story 1.10) and the verdict/breakdown (Story 1.11)
// fill these regions next.

import { ThemeToggle } from './components/ThemeToggle.tsx'

export default function App() {
  return (
    <div className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
        <h1 className="text-lg font-bold tracking-tight">
          vllm<span className="text-[var(--accent)]">-calc</span>
        </h1>
        <ThemeToggle />
      </header>

      <main className="grid flex-1 gap-6 p-6 lg:grid-cols-[minmax(320px,420px)_1fr]">
        <section
          aria-label="Configuration"
          data-testid="inputs-region"
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
        >
          <p className="text-sm text-[var(--muted)]">Inputs — coming in Story 1.10.</p>
        </section>

        <section
          aria-label="Result"
          data-testid="result-region"
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
        >
          <p className="text-sm text-[var(--muted)]">
            Verdict &amp; VRAM breakdown — coming in Story 1.11.
          </p>
        </section>
      </main>
    </div>
  )
}
