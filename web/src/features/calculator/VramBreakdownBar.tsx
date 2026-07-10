import type { Breakdown } from '../../api/types.ts'

const GIB = 1024 ** 3
const gib = (b: number): string => `${(b / GIB).toFixed(1)} GiB`
const pct = (b: number, scale: number): number => (scale > 0 ? (b / scale) * 100 : 0)

// Colorblind-safe categorical trio (indigo / teal / slate), held distinct from
// the semantic fit/no-fit/warn status colors. Meaning never relies on color
// alone — every segment is also labeled in the legend and the screen-reader table.
const C = { weights: '#4f46e5', kv: '#0d9488', overhead: '#94a3b8' }

export function VramBreakdownBar({ breakdown: b }: { breakdown: Breakdown }) {
  const scale = Math.max(b.used_per_gpu_bytes, b.budget_per_gpu_bytes)
  const label =
    `Per-GPU VRAM: weights ${gib(b.weights_per_gpu_bytes)}, KV cache ${gib(b.kv_per_gpu_bytes)}, ` +
    `overhead ${gib(b.overhead_total_bytes)}; used ${gib(b.used_per_gpu_bytes)} of a ` +
    `${gib(b.budget_per_gpu_bytes)} budget.`

  const seg = (bytes: number, color: string, title: string) => (
    <div
      title={`${title}: ${gib(bytes)}`}
      className="h-full transition-[width] duration-200 motion-reduce:transition-none"
      style={{ width: `${pct(bytes, scale)}%`, background: color }}
    />
  )

  return (
    <figure className="m-0">
      <div className="mb-1 flex justify-between text-xs text-[var(--muted)]">
        <span>Per-GPU VRAM</span>
        <span className="font-mono tabular-nums">
          {gib(b.used_per_gpu_bytes)} / {gib(b.budget_per_gpu_bytes)}
        </span>
      </div>

      <div
        role="img"
        aria-label={label}
        className="relative flex h-7 overflow-hidden rounded-md border border-[var(--border)] bg-[var(--surface-2)]"
      >
        {seg(b.weights_per_gpu_bytes, C.weights, 'Weights')}
        {seg(b.kv_per_gpu_bytes, C.kv, 'KV cache')}
        {seg(b.overhead_total_bytes, C.overhead, 'Overhead')}
        <div
          aria-hidden="true"
          className="absolute top-[-3px] bottom-[-3px] w-0.5 bg-[var(--ink)]"
          style={{ left: `${pct(b.budget_per_gpu_bytes, scale)}%` }}
        />
      </div>

      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--muted)]">
        {(
          [
            ['Weights', C.weights, b.weights_per_gpu_bytes],
            ['KV cache', C.kv, b.kv_per_gpu_bytes],
            ['Overhead', C.overhead, b.overhead_total_bytes],
          ] as const
        ).map(([name, color, bytes]) => (
          <li key={name} className="flex items-center gap-1.5">
            <span aria-hidden="true" className="h-2.5 w-2.5 rounded-sm" style={{ background: color }} />
            {name} <span className="font-mono tabular-nums">{gib(bytes)}</span>
          </li>
        ))}
      </ul>

      <details className="mt-2 text-xs text-[var(--muted)]">
        <summary className="cursor-pointer">Show overhead breakdown</summary>
        <dl className="mt-1 grid grid-cols-2 gap-x-4 font-mono tabular-nums">
          <dt>Fixed context (+NCCL)</dt>
          <dd>{gib(b.overhead_fixed_context_bytes)}</dd>
          <dt>Activations</dt>
          <dd>{gib(b.overhead_activations_bytes)}</dd>
          <dt>CUDA graphs</dt>
          <dd>{gib(b.overhead_cuda_graphs_bytes)}</dd>
        </dl>
      </details>

      {/* Screen-reader alternative to the visual bar. */}
      <table className="sr-only">
        <caption>Per-GPU VRAM breakdown</caption>
        <tbody>
          <tr>
            <th scope="row">Weights</th>
            <td>{gib(b.weights_per_gpu_bytes)}</td>
          </tr>
          <tr>
            <th scope="row">KV cache</th>
            <td>{gib(b.kv_per_gpu_bytes)}</td>
          </tr>
          <tr>
            <th scope="row">Overhead</th>
            <td>{gib(b.overhead_total_bytes)}</td>
          </tr>
          <tr>
            <th scope="row">Budget</th>
            <td>{gib(b.budget_per_gpu_bytes)}</td>
          </tr>
        </tbody>
      </table>
    </figure>
  )
}
