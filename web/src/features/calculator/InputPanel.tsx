import { type ReactNode, useState } from 'react'

import type { CalcInput, GpuPreset, ModelPreset } from '../../api/types.ts'

interface Props {
  input: CalcInput
  setInput: (patch: Partial<CalcInput>) => void
  modelPresets: ModelPreset[]
  gpuPresets: GpuPreset[]
}

const fieldCls =
  'w-full rounded-md border border-[var(--border)] bg-[var(--surface-2)] px-2.5 py-1.5 text-sm'

/** Derive the `vllm serve` model reference (HF repo id) from a preset's source
 *  URL, e.g. https://huggingface.co/meta-llama/Llama-3.3-70B → the repo id.
 *  Non-HF sources yield null so the command shows its swap-me placeholder. */
function hfIdFromSource(source: string): string | null {
  const m = /huggingface\.co\/([^?#]+)/.exec(source)
  return m ? m[1].replace(/\/$/, '') : null
}

function NumberField(props: {
  label: string
  value: number
  onChange: (v: number) => void
  step?: number
}) {
  return (
    <label className="block text-xs text-[var(--muted)]">
      {props.label}
      <input
        type="number"
        className={`mt-1 font-mono ${fieldCls}`}
        value={props.value}
        step={props.step}
        onChange={(e) => props.onChange(Number(e.target.value))}
      />
    </label>
  )
}

function Group(props: { legend: string; children: ReactNode }) {
  return (
    <fieldset className="mb-4 border-0 p-0">
      <legend className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
        {props.legend}
      </legend>
      <div className="grid grid-cols-2 gap-3">{props.children}</div>
    </fieldset>
  )
}

export function InputPanel({ input, setInput, modelPresets, gpuPresets }: Props) {
  const [modelId, setModelId] = useState('')
  const [gpuId, setGpuId] = useState('')

  function selectModel(id: string) {
    setModelId(id)
    if (id === 'custom') {
      setInput({ model_ref: null }) // custom model → command shows the placeholder
      return
    }
    const p = modelPresets.find((m) => m.id === id)
    if (p)
      setInput({
        model_ref: hfIdFromSource(p.source),
        total_params: p.total_params,
        layers: p.layers,
        attention_heads: p.attention_heads,
        kv_heads: p.kv_heads,
        head_dim: p.head_dim,
        hidden_size: p.hidden_size,
      })
  }

  function selectGpu(id: string) {
    setGpuId(id)
    const g = gpuPresets.find((x) => x.id === id)
    if (g) setInput({ gpu_vram_gib: g.vram_gib })
  }

  const fromPreset = modelId && modelId !== 'custom'

  return (
    <div>
      <Group legend="Model">
        <label className="col-span-2 block text-xs text-[var(--muted)]">
          Preset
          <select
            aria-label="Model preset"
            className={`mt-1 ${fieldCls}`}
            value={modelId}
            onChange={(e) => selectModel(e.target.value)}
          >
            <option value="">— choose a model —</option>
            {modelPresets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
            <option value="custom">Custom…</option>
          </select>
        </label>

        {fromPreset && (
          <p className="col-span-2 -mt-1 text-[11px] text-[var(--accent)]">
            ◆ architecture from preset (editable)
          </p>
        )}

        <NumberField
          label="Total params"
          value={input.total_params}
          onChange={(v) => setInput({ total_params: v })}
        />
        <NumberField label="Layers" value={input.layers} onChange={(v) => setInput({ layers: v })} />
        <NumberField
          label="Attention heads"
          value={input.attention_heads}
          onChange={(v) => setInput({ attention_heads: v })}
        />
        <NumberField
          label="KV heads"
          value={input.kv_heads}
          onChange={(v) => setInput({ kv_heads: v })}
        />
        <NumberField
          label="Head dim"
          value={input.head_dim}
          onChange={(v) => setInput({ head_dim: v })}
        />
        <NumberField
          label="Hidden size"
          value={input.hidden_size}
          onChange={(v) => setInput({ hidden_size: v })}
        />
        <label className="col-span-2 block text-xs text-[var(--muted)]">
          Quantization
          <select
            aria-label="Quantization"
            className={`mt-1 ${fieldCls}`}
            value={input.weight_quant}
            onChange={(e) => setInput({ weight_quant: e.target.value as CalcInput['weight_quant'] })}
          >
            {['fp16', 'bf16', 'fp8', 'int8', 'awq-4bit', 'gptq-4bit', 'fp32'].map((q) => (
              <option key={q} value={q}>
                {q}
              </option>
            ))}
          </select>
        </label>
      </Group>

      <Group legend="GPU & Parallelism">
        <label className="col-span-2 block text-xs text-[var(--muted)]">
          GPU preset
          <select
            aria-label="GPU preset"
            className={`mt-1 ${fieldCls}`}
            value={gpuId}
            onChange={(e) => selectGpu(e.target.value)}
          >
            <option value="">— choose a GPU —</option>
            {gpuPresets.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
            <option value="custom">Custom…</option>
          </select>
        </label>
        <NumberField
          label="VRAM per GPU (GiB)"
          value={input.gpu_vram_gib}
          onChange={(v) => setInput({ gpu_vram_gib: v })}
        />
        <NumberField
          label="GPU count"
          value={input.gpu_count}
          onChange={(v) => setInput({ gpu_count: v })}
        />
        <NumberField
          label="Tensor parallel"
          value={input.tensor_parallel_size}
          onChange={(v) => setInput({ tensor_parallel_size: v })}
        />
      </Group>

      <Group legend="Workload">
        <NumberField
          label="Context length"
          value={input.ctx_len}
          onChange={(v) => setInput({ ctx_len: v })}
        />
        <NumberField
          label="Max sequences"
          value={input.max_seqs}
          onChange={(v) => setInput({ max_seqs: v })}
        />
        <NumberField
          label="GPU mem util"
          step={0.05}
          value={input.gpu_memory_utilization}
          onChange={(v) => setInput({ gpu_memory_utilization: v })}
        />
        <label className="block text-xs text-[var(--muted)]">
          KV cache dtype
          <select
            aria-label="KV cache dtype"
            className={`mt-1 ${fieldCls}`}
            value={input.kv_dtype}
            onChange={(e) => setInput({ kv_dtype: e.target.value as CalcInput['kv_dtype'] })}
          >
            {['fp16', 'bf16', 'fp8'].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
      </Group>

      <details className="text-sm">
        <summary className="cursor-pointer text-[var(--muted)]">Advanced</summary>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <NumberField
            label="Max batched tokens"
            value={input.max_num_batched_tokens}
            onChange={(v) => setInput({ max_num_batched_tokens: v })}
          />
          <NumberField
            label="Max seqs cap"
            value={input.max_num_seqs_cap}
            onChange={(v) => setInput({ max_num_seqs_cap: v })}
          />
          <label className="col-span-2 flex items-center gap-2 text-xs text-[var(--muted)]">
            <input
              type="checkbox"
              checked={input.enforce_eager}
              onChange={(e) => setInput({ enforce_eager: e.target.checked })}
            />
            enforce_eager (disable CUDA graphs)
          </label>
        </div>
      </details>
    </div>
  )
}
