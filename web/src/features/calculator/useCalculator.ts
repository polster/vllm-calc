import { useEffect, useRef, useState } from 'react'

import {
  fetchGpuPresets,
  fetchModelPresets,
  postCalculate,
} from '../../api/client.ts'
import type { CalcInput, CalcResult, GpuPreset, ModelPreset } from '../../api/types.ts'
import type { UiSelection } from './defaults.ts'
import { decodeState, encodeState } from './urlState.ts'

export type Status = 'loading' | 'ready' | 'error'

export interface CalculatorDeps {
  calculate: (input: CalcInput) => Promise<CalcResult>
  fetchModels: () => Promise<ModelPreset[]>
  fetchGpus: () => Promise<GpuPreset[]>
}

const DEFAULT_DEPS: CalculatorDeps = {
  calculate: postCalculate,
  fetchModels: fetchModelPresets,
  fetchGpus: fetchGpuPresets,
}

const DEBOUNCE_MS = 250

/** Owns the calculator's state: input config, curated presets, and a debounced
 *  live recompute against the API. The last VALID result persists across errors
 *  (never blanks out); a request-sequence guard drops stale responses. */
export function useCalculator(deps: CalculatorDeps = DEFAULT_DEPS) {
  const { calculate, fetchModels, fetchGpus } = deps

  // Seed from the URL so a shared/refreshed scenario is restored (UX-DR8);
  // an empty query yields the default scenario and its preset selection.
  // Decoded once (lazy initializer), not on every render.
  const [initial] = useState(() =>
    decodeState(typeof window === 'undefined' ? '' : window.location.search),
  )
  const [input, setInputState] = useState<CalcInput>(initial.input)
  const [selection, setSelectionState] = useState<UiSelection>(initial.selection)
  const [result, setResult] = useState<CalcResult | null>(null)
  const [status, setStatus] = useState<Status>('loading')
  const [error, setError] = useState<string | null>(null)
  const [modelPresets, setModelPresets] = useState<ModelPreset[]>([])
  const [gpuPresets, setGpuPresets] = useState<GpuPreset[]>([])

  const seq = useRef(0)

  useEffect(() => {
    let alive = true
    fetchModels().then((p) => alive && setModelPresets(p)).catch(() => {})
    fetchGpus().then((p) => alive && setGpuPresets(p)).catch(() => {})
    return () => {
      alive = false
    }
  }, [fetchModels, fetchGpus])

  // Restore the scenario and its dropdown selection on browser back/forward.
  useEffect(() => {
    const onPop = () => {
      const s = decodeState(window.location.search)
      setInputState(s.input)
      setSelectionState(s.selection)
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  useEffect(() => {
    setStatus('loading')
    const requestId = ++seq.current
    const handle = setTimeout(() => {
      calculate(input)
        .then((r) => {
          if (requestId !== seq.current) return // stale response, drop
          setResult(r) // last-valid result
          setStatus('ready')
          setError(null)
        })
        .catch((e: unknown) => {
          if (requestId !== seq.current) return
          setError(e instanceof Error ? e.message : 'Calculation failed.')
          setStatus('error') // keep the previous `result` visible
        })
    }, DEBOUNCE_MS)
    return () => clearTimeout(handle)
  }, [input, calculate])

  // Keep the URL in sync with the scenario AND the dropdown selection (a GPU
  // pick sharing another preset's VRAM changes only `selection`); replaceState
  // (debounced) avoids flooding history while keeping the URL copy-shareable.
  useEffect(() => {
    const handle = setTimeout(() => {
      window.history.replaceState(
        null,
        '',
        `${window.location.pathname}?${encodeState(input, selection)}`,
      )
    }, DEBOUNCE_MS)
    return () => clearTimeout(handle)
  }, [input, selection])

  function setInput(patch: Partial<CalcInput>): void {
    setInputState((prev) => ({ ...prev, ...patch }))
  }

  function setSelection(patch: Partial<UiSelection>): void {
    setSelectionState((prev) => ({ ...prev, ...patch }))
  }

  return {
    input,
    setInput,
    selection,
    setSelection,
    result,
    status,
    error,
    modelPresets,
    gpuPresets,
  }
}
