import * as Tooltip from '@radix-ui/react-tooltip'

/**
 * An accessible info affordance placed next to a field label. The trigger is a
 * real focusable button (hover AND keyboard focus open it, Esc/blur dismiss it);
 * the description is exposed to assistive tech through Radix's ARIA wiring.
 *
 * Must be rendered inside a single `Tooltip.Provider` (see InputPanel).
 */
export function FieldTooltip({ label, description }: { label: string; description: string }) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button
          type="button"
          aria-label={`About ${label}`}
          className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-[var(--border)] text-[10px] font-semibold leading-none text-[var(--muted)] transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"
        >
          <span aria-hidden="true">i</span>
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          side="top"
          align="start"
          sideOffset={6}
          collisionPadding={8}
          className="z-50 max-w-[16rem] rounded-md border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-xs leading-snug text-[var(--ink)] shadow-md"
        >
          {description}
          <Tooltip.Arrow className="fill-[var(--surface)]" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  )
}
