import type { CalcResult } from '../../api/types.ts'

/** The answer: go/no-go + capacity, as the visual center of gravity. Status is
 *  carried by icon + text + color (never color alone, NFR17). Wrapped in a polite
 *  ARIA live region so a recompute's new verdict is announced to screen readers. */
export function VerdictBanner({ result }: { result: CalcResult }) {
  const color = result.fits ? 'var(--fit)' : 'var(--no-fit)'
  return (
    <div
      aria-live="polite"
      className="rounded-lg border p-4"
      style={{ borderColor: color, background: 'color-mix(in srgb, ' + color + ' 10%, transparent)' }}
    >
      <p className="flex items-center gap-2 text-lg font-semibold" style={{ color }}>
        <span
          aria-hidden="true"
          className="grid h-7 w-7 place-items-center rounded-full text-sm text-white"
          style={{ background: color }}
        >
          {result.fits ? '✓' : '✗'}
        </span>
        <span>{result.fits ? 'Fits' : "Won't fit"}</span>
      </p>
      <p className="mt-1 text-sm text-[var(--ink)]">{result.verdict}</p>
      <p className="mt-1 text-[11px] text-[var(--muted)]">
        calibrated for vLLM {result.supported_vllm_range}
      </p>
    </div>
  )
}
