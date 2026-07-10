import { useEffect, useRef, useState } from 'react'

/** Renders the engine-generated `vllm serve` command in a monospace block with
 *  syntax-tinted flags and a copy affordance. The command comes from the engine
 *  (CalcResult.serve_command) — the SPA only tokenizes it for display, never
 *  builds it (parity, NFR3). */
export function CommandBlock({ command }: { command: string }) {
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(
    () => () => {
      if (timer.current !== null) clearTimeout(timer.current)
    },
    [],
  )

  async function copy() {
    try {
      await navigator.clipboard?.writeText(command)
      setCopied(true)
      if (timer.current !== null) clearTimeout(timer.current)
      timer.current = setTimeout(() => setCopied(false), 1800)
    } catch {
      // Clipboard denied/unavailable — leave the text selectable for manual copy.
    }
  }

  const tokens = command.split(' ')

  return (
    <figure className="m-0">
      <figcaption className="mb-1 flex items-center justify-between text-xs text-[var(--muted)]">
        <span>Run it</span>
        <button
          type="button"
          onClick={copy}
          className="rounded-md border border-[var(--border)] px-2 py-0.5 text-xs hover:bg-[var(--surface-2)]"
        >
          {copied ? 'Copied ✓' : 'Copy'}
        </button>
      </figcaption>

      <pre className="overflow-x-auto rounded-md border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs leading-relaxed">
        <code className="font-mono">
          {tokens.map((tok, i) => (
            <span key={i}>
              {i > 0 && ' '}
              <span className={tok.startsWith('--') ? 'text-[var(--accent)]' : undefined}>
                {tok}
              </span>
            </span>
          ))}
        </code>
      </pre>

      {/* Announce the copy result to assistive tech without moving focus. */}
      <span aria-live="polite" className="sr-only">
        {copied ? 'Command copied to clipboard' : ''}
      </span>
    </figure>
  )
}
