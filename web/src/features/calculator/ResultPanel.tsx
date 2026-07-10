import type { CalcInput, CalcResult } from '../../api/types.ts'
import { CommandBlock } from './CommandBlock.tsx'
import { RemediationChips } from './RemediationChips.tsx'
import { VerdictBanner } from './VerdictBanner.tsx'
import { VramBreakdownBar } from './VramBreakdownBar.tsx'
import type { Status } from './useCalculator.ts'

interface Props {
  result: CalcResult | null
  status: Status
  error: string | null
  onApply?: (delta: Partial<CalcInput>) => void
}

/** The result region: verdict banner + VRAM breakdown. The last valid result
 *  stays visible during recompute (dimmed, not blanked) and across errors. */
export function ResultPanel({ result, status, error, onApply }: Props) {
  return (
    <div aria-busy={status === 'loading'} className="flex flex-col gap-4">
      {error && (
        <p role="alert" className="rounded-md border border-[var(--no-fit)] px-3 py-2 text-sm">
          {error} <span className="text-[var(--muted)]">(showing last valid result)</span>
        </p>
      )}

      {!result ? (
        <p className="text-sm text-[var(--muted)]">Calculating…</p>
      ) : (
        <div
          className={
            status === 'loading'
              ? 'flex flex-col gap-4 opacity-60 transition-opacity motion-reduce:transition-none'
              : 'flex flex-col gap-4'
          }
        >
          <VerdictBanner result={result} />
          {onApply && (
            <RemediationChips remediations={result.remediations} onApply={onApply} />
          )}
          <VramBreakdownBar breakdown={result.breakdown} />
          <CommandBlock command={result.serve_command} />

          {result.warnings.map((w) => (
            <p key={w} className="text-xs" style={{ color: 'var(--warn)' }}>
              ⚠ {w}
            </p>
          ))}

          <p className="text-[11px] text-[var(--muted)]">{result.worst_case_note}</p>
        </div>
      )}
    </div>
  )
}
