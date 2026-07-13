import type { Flag } from '../../api/types.ts'

/** Calm amber callouts for honesty flags (MLA/SWA over-provision, uncalibrated
 *  architectures). Never alarming — these explain why a number is conservative
 *  or uncertain rather than hiding it. Uses the reserved --warn status token with
 *  an icon + text (not color alone). */
export function HonestyCallout({ flags }: { flags: Flag[] }) {
  if (flags.length === 0) return null

  return (
    <div className="flex flex-col gap-2">
      {flags.map((f, i) => (
        <div
          key={`${i}-${f.type}`}
          role="note"
          className="flex gap-2 rounded-md border px-3 py-2 text-xs"
          style={{
            borderColor: 'var(--warn)',
            background: 'color-mix(in srgb, var(--warn) 10%, transparent)',
          }}
        >
          <span aria-hidden="true" style={{ color: 'var(--warn)' }}>
            ⚠
          </span>
          <span className="text-[var(--ink)]">
            <span className="font-semibold">
              {f.type === 'unsupported' ? 'Not calibrated' : 'Conservative estimate'}
            </span>{' '}
            {f.message}
          </span>
        </div>
      ))}
    </div>
  )
}
