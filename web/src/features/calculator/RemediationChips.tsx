import type { CalcInput, Remediation } from '../../api/types.ts'

/** On a no-go, actionable "nearest fitting config" chips. Each carries the exact
 *  input delta the engine computed; clicking applies it through the normal
 *  live-recompute path (the SPA does no sizing of its own). */
export function RemediationChips({
  remediations,
  onApply,
}: {
  remediations: Remediation[]
  onApply: (delta: Partial<CalcInput>) => void
}) {
  if (remediations.length === 0) return null

  return (
    <div>
      <p className="mb-1.5 text-xs text-[var(--muted)]">Ways to make it fit</p>
      <ul className="flex flex-wrap gap-2">
        {remediations.map((r) => (
          <li key={r.label}>
            <button
              type="button"
              onClick={() => onApply(r.delta)}
              title={r.detail}
              className="rounded-full border border-[var(--accent)] px-3 py-1 text-xs text-[var(--accent)] hover:bg-[color-mix(in_srgb,var(--accent)_12%,transparent)]"
            >
              {r.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
