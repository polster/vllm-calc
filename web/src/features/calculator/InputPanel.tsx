import * as Tooltip from '@radix-ui/react-tooltip'
import { type ReactNode, useId } from 'react'

import type { CalcInput, GpuPreset, ModelPreset } from '../../api/types.ts'
import type { UiSelection } from './defaults.ts'
import { FieldTooltip } from './FieldTooltip.tsx'
import { FIELD_HELP, PICKER_HELP } from './fieldHelp.ts'

interface Props {
  input: CalcInput
  setInput: (patch: Partial<CalcInput>) => void
  selection: UiSelection
  setSelection: (patch: Partial<UiSelection>) => void
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

/** Label row: a real `<label htmlFor>` (so clicking the text focuses the
 *  control) plus, when help is supplied, an accessible info tooltip rendered
 *  as a sibling — never nested in the label, so it neither pollutes the
 *  control's accessible name nor hijacks the label's click target. */
function FieldLabel(props: { htmlFor: string; text: string; help?: string }) {
  return (
    <span className="mb-1 flex items-center gap-1.5">
      <label htmlFor={props.htmlFor}>{props.text}</label>
      {props.help && <FieldTooltip label={props.text} description={props.help} />}
    </span>
  )
}

function NumberField(props: {
  label: string
  value: number
  onChange: (v: number) => void
  step?: number
  help?: string
}) {
  const id = useId()
  return (
    <div className="block text-xs text-[var(--muted)]">
      <FieldLabel htmlFor={id} text={props.label} help={props.help} />
      <input
        id={id}
        type="number"
        className={`font-mono ${fieldCls}`}
        value={props.value}
        step={props.step}
        onChange={(e) => props.onChange(Number(e.target.value))}
      />
    </div>
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

export function InputPanel({
  input,
  setInput,
  selection,
  setSelection,
  modelPresets,
  gpuPresets,
}: Props) {
  const { modelPresetId, gpuPresetId } = selection
  const selectedModel = modelPresets.find((m) => m.id === modelPresetId)
  const selectedGpu = gpuPresets.find((g) => g.id === gpuPresetId)

  // The persisted selection can name a preset that isn't in the (async-loaded)
  // list yet, or at all (a stale shared link). Bind the control to a value that
  // actually has an <option> so it degrades to the placeholder instead of
  // rendering blank with a value that matches nothing.
  const modelValue = selectedModel || modelPresetId === 'custom' ? modelPresetId : ''
  const gpuValue = selectedGpu || gpuPresetId === 'custom' ? gpuPresetId : ''

  const modelPresetFieldId = useId()
  const quantFieldId = useId()
  const gpuPresetFieldId = useId()
  const kvDtypeFieldId = useId()

  function selectModel(id: string) {
    setSelection({ modelPresetId: id })
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
        attention_type: p.attention_type,
      })
  }

  function selectGpu(id: string) {
    setSelection({ gpuPresetId: id })
    const g = gpuPresets.find((x) => x.id === id)
    if (g) setInput({ gpu_vram_gib: g.vram_gib })
  }

  // Only treat it as "from a preset" when the preset actually resolves — a
  // loading/unknown id must not claim the architecture came from a preset.
  const fromPreset = Boolean(selectedModel)
  const selectedPurpose = selectedModel?.purpose

  return (
    <Tooltip.Provider delayDuration={200}>
      <div>
        <Group legend="Model">
          <div className="col-span-2 block text-xs text-[var(--muted)]">
            <FieldLabel htmlFor={modelPresetFieldId} text="Preset" help={PICKER_HELP.model_preset} />
            <select
              id={modelPresetFieldId}
              aria-label="Model preset"
              className={fieldCls}
              value={modelValue}
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
          </div>

          {selectedPurpose && (
            <p className="col-span-2 -mt-1 text-[11px] text-[var(--muted)]">
              {selectedPurpose}
            </p>
          )}

          {fromPreset && (
            <p className="col-span-2 -mt-1 text-[11px] text-[var(--accent)]">
              ◆ architecture from preset (editable)
            </p>
          )}

          <NumberField
            label="Total params"
            help={FIELD_HELP.total_params}
            value={input.total_params}
            onChange={(v) => setInput({ total_params: v })}
          />
          <NumberField
            label="Layers"
            help={FIELD_HELP.layers}
            value={input.layers}
            onChange={(v) => setInput({ layers: v })}
          />
          <NumberField
            label="Attention heads"
            help={FIELD_HELP.attention_heads}
            value={input.attention_heads}
            onChange={(v) => setInput({ attention_heads: v })}
          />
          <NumberField
            label="KV heads"
            help={FIELD_HELP.kv_heads}
            value={input.kv_heads}
            onChange={(v) => setInput({ kv_heads: v })}
          />
          <NumberField
            label="Head dim"
            help={FIELD_HELP.head_dim}
            value={input.head_dim}
            onChange={(v) => setInput({ head_dim: v })}
          />
          <NumberField
            label="Hidden size"
            help={FIELD_HELP.hidden_size}
            value={input.hidden_size}
            onChange={(v) => setInput({ hidden_size: v })}
          />
          <div className="col-span-2 block text-xs text-[var(--muted)]">
            <FieldLabel htmlFor={quantFieldId} text="Quantization" help={FIELD_HELP.weight_quant} />
            <select
              id={quantFieldId}
              className={fieldCls}
              value={input.weight_quant}
              onChange={(e) => setInput({ weight_quant: e.target.value as CalcInput['weight_quant'] })}
            >
              {['fp16', 'bf16', 'fp8', 'int8', 'awq-4bit', 'gptq-4bit', 'fp32'].map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>
        </Group>

        <Group legend="GPU & Parallelism">
          <div className="col-span-2 block text-xs text-[var(--muted)]">
            <FieldLabel htmlFor={gpuPresetFieldId} text="GPU preset" help={PICKER_HELP.gpu_preset} />
            <select
              id={gpuPresetFieldId}
              aria-label="GPU preset"
              className={fieldCls}
              value={gpuValue}
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
          </div>
          <NumberField
            label="VRAM per GPU (GiB)"
            help={FIELD_HELP.gpu_vram_gib}
            value={input.gpu_vram_gib}
            onChange={(v) => setInput({ gpu_vram_gib: v })}
          />
          <NumberField
            label="GPU count"
            help={FIELD_HELP.gpu_count}
            value={input.gpu_count}
            onChange={(v) => setInput({ gpu_count: v })}
          />
          <NumberField
            label="Tensor parallel"
            help={FIELD_HELP.tensor_parallel_size}
            value={input.tensor_parallel_size}
            onChange={(v) => setInput({ tensor_parallel_size: v })}
          />
        </Group>

        <Group legend="Workload">
          <NumberField
            label="Context length"
            help={FIELD_HELP.ctx_len}
            value={input.ctx_len}
            onChange={(v) => setInput({ ctx_len: v })}
          />
          <NumberField
            label="Max sequences"
            help={FIELD_HELP.max_seqs}
            value={input.max_seqs}
            onChange={(v) => setInput({ max_seqs: v })}
          />
          <NumberField
            label="GPU mem util"
            help={FIELD_HELP.gpu_memory_utilization}
            step={0.05}
            value={input.gpu_memory_utilization}
            onChange={(v) => setInput({ gpu_memory_utilization: v })}
          />
          <div className="block text-xs text-[var(--muted)]">
            <FieldLabel htmlFor={kvDtypeFieldId} text="KV cache dtype" help={FIELD_HELP.kv_dtype} />
            <select
              id={kvDtypeFieldId}
              className={fieldCls}
              value={input.kv_dtype}
              onChange={(e) => setInput({ kv_dtype: e.target.value as CalcInput['kv_dtype'] })}
            >
              {['fp16', 'bf16', 'fp8'].map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        </Group>

        <details className="text-sm">
          <summary className="cursor-pointer text-[var(--muted)]">Advanced</summary>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <NumberField
              label="Max batched tokens"
              help={FIELD_HELP.max_num_batched_tokens}
              value={input.max_num_batched_tokens}
              onChange={(v) => setInput({ max_num_batched_tokens: v })}
            />
            <NumberField
              label="Max seqs cap"
              help={FIELD_HELP.max_num_seqs_cap}
              value={input.max_num_seqs_cap}
              onChange={(v) => setInput({ max_num_seqs_cap: v })}
            />
            <div className="col-span-2 flex items-center gap-2 text-xs text-[var(--muted)]">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={input.enforce_eager}
                  onChange={(e) => setInput({ enforce_eager: e.target.checked })}
                />
                enforce_eager (disable CUDA graphs)
              </label>
              <FieldTooltip label="enforce_eager" description={FIELD_HELP.enforce_eager} />
            </div>
          </div>
        </details>
      </div>
    </Tooltip.Provider>
  )
}
