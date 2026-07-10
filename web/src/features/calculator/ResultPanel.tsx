import type { CalcResult } from '../../api/types.ts'
import type { Status } from './useCalculator.ts'

const GIB = 1024 ** 3
const gib = (bytes: number): string => `${(bytes / GIB).toFixed(1)} GiB`

interface Props {
  result: CalcResult | null
  status: Status
  error: string | null
}

/** Minimal inline result for Story 1.10. Story 1.11 replaces this with the
 *  designed VerdictBanner + VramBreakdownBar (the last valid result stays visible
 *  during recompute/errors — never blanks out). */
export function ResultPanel({ result, status, error }: Props) {
  return (
    <div aria-busy={status === 'loading'}>
      {error && (
        <p role="alert" className="mb-3 rounded-md border border-[var(--no-fit)] px-3 py-2 text-sm">
          {error} <span className="text-[var(--muted)]">(showing last valid result)</span>
        </p>
      )}

      {!result ? (
        <p className="text-sm text-[var(--muted)]">Calculating…</p>
      ) : (
        <div className={status === 'loading' ? 'opacity-60 transition-opacity' : ''}>
          <p
            className="text-lg font-semibold"
            style={{ color: result.fits ? 'var(--fit)' : 'var(--no-fit)' }}
          >
            {result.fits ? '✓' : '✗'} {result.verdict}
          </p>

          <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 font-mono text-sm tabular-nums">
            <dt className="text-[var(--muted)]">Weights / GPU</dt>
            <dd>{gib(result.breakdown.weights_per_gpu_bytes)}</dd>
            <dt className="text-[var(--muted)]">KV cache / GPU</dt>
            <dd>{gib(result.breakdown.kv_per_gpu_bytes)}</dd>
            <dt className="text-[var(--muted)]">Overhead / GPU</dt>
            <dd>{gib(result.breakdown.overhead_total_bytes)}</dd>
            <dt className="text-[var(--muted)]">Used / budget</dt>
            <dd>
              {gib(result.breakdown.used_per_gpu_bytes)} /{' '}
              {gib(result.breakdown.budget_per_gpu_bytes)}
            </dd>
            <dt className="text-[var(--muted)]">Max concurrent</dt>
            <dd>{result.max_concurrent}</dd>
          </dl>

          {result.warnings.map((w) => (
            <p key={w} className="mt-2 text-xs" style={{ color: 'var(--warn)' }}>
              ⚠ {w}
            </p>
          ))}

          <p className="mt-3 text-[11px] text-[var(--muted)]">
            {result.worst_case_note} · calibrated for vLLM {result.supported_vllm_range}
          </p>
        </div>
      )}
    </div>
  )
}
