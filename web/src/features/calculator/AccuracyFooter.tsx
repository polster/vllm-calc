import { useEffect, useState } from 'react'

import { fetchValidation } from '../../api/client.ts'
import type { ValidationStatus } from '../../api/types.ts'

/** A quiet footer that surfaces the published accuracy status at the point of use
 *  (UX honesty / Story 4.4). Shows the measured pass rate once the GPU runner has
 *  published one, and always states the calibrated vLLM range. */
export function AccuracyFooter({
  fetch = fetchValidation,
}: {
  fetch?: () => Promise<ValidationStatus>
}) {
  const [v, setV] = useState<ValidationStatus | null>(null)

  useEffect(() => {
    let alive = true
    fetch()
      .then((s) => alive && setV(s))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [fetch])

  if (!v) return null

  const accuracy =
    v.status === 'validated' && v.pass_rate != null
      ? `Accuracy: ${Math.round(v.pass_rate * 100)}% of cases within ±10% (measured against real vLLM)`
      : 'Accuracy: not yet validated against real vLLM'

  return (
    <footer className="border-t border-[var(--border)] px-6 py-3 text-[11px] text-[var(--muted)]">
      {accuracy} · calibrated for vLLM {v.calibrated_vllm_range}
    </footer>
  )
}
