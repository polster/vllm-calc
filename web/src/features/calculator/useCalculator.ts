import { useEffect, useRef, useState } from 'react'

import {
  fetchGpuPresets,
  fetchModelPresets,
  postCalculate,
} from '../../api/client.ts'
import type { CalcInput, CalcResult, GpuPreset, ModelPreset } from '../../api/types.ts'
import { decodeInput, encodeInput } from './urlState.ts'

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
  // an empty query yields the default scenario.
  const [input, setInputState] = useState<CalcInput>(() =>
    decodeInput(typeof window === 'undefined' ? '' : window.location.search),
  )
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

  // Restore the scenario on browser back/forward.
  useEffect(() => {
    const onPop = () => setInputState(decodeInput(window.location.search))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  useEffect(() => {
    setStatus('loading')
    const requestId = ++seq.current
    const handle = setTimeout(() => {
      // Keep the URL in sync (debounced with the recompute); replaceState avoids
      // flooding history on every keystroke while keeping the URL copy-shareable.
      window.history.replaceState(null, '', `${window.location.pathname}?${encodeInput(input)}`)
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

  function setInput(patch: Partial<CalcInput>): void {
    setInputState((prev) => ({ ...prev, ...patch }))
  }

  return { input, setInput, result, status, error, modelPresets, gpuPresets }
}
