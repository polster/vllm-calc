import { InputPanel } from './InputPanel.tsx'
import { ResultPanel } from './ResultPanel.tsx'
import { useCalculator } from './useCalculator.ts'

/** The two-region calculator: inputs drive a debounced live recompute; the
 *  result region shows the verdict + breakdown. */
export function CalculatorPage() {
  const { input, setInput, result, status, error, modelPresets, gpuPresets } = useCalculator()

  return (
    <main className="grid flex-1 gap-6 p-6 lg:grid-cols-[minmax(320px,420px)_1fr]">
      <section
        aria-label="Configuration"
        data-testid="inputs-region"
        className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
      >
        <InputPanel
          input={input}
          setInput={setInput}
          modelPresets={modelPresets}
          gpuPresets={gpuPresets}
        />
      </section>

      <section
        aria-label="Result"
        data-testid="result-region"
        className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
      >
        <ResultPanel result={result} status={status} error={error} onApply={setInput} />
      </section>
    </main>
  )
}
