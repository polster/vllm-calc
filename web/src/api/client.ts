/** Thin typed client for the vllm-calc API. The SPA holds NO calculation logic
 *  (parity invariant) — it only calls the backend. Base URL is configurable so
 *  the same build points at the public API or a local/Docker backend. */

import type {
  ApiErrorBody,
  CalcInput,
  CalcResult,
  GpuPreset,
  ModelPreset,
  ValidationStatus,
} from './types.ts'

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

/** A calculation failed with a structured error from the API. */
export class ApiError extends Error {
  readonly type: string
  constructor(body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiError'
    this.type = body.type
  }
}

async function getJson<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`)
  if (!resp.ok) throw new Error(`GET ${path} failed: ${resp.status}`)
  return (await resp.json()) as T
}

export async function fetchModelPresets(): Promise<ModelPreset[]> {
  return getJson<ModelPreset[]>('/v1/presets/models')
}

export async function fetchGpuPresets(): Promise<GpuPreset[]> {
  return getJson<GpuPreset[]>('/v1/presets/gpus')
}

export async function fetchValidation(): Promise<ValidationStatus> {
  return getJson<ValidationStatus>('/v1/validation')
}

/** POST a config to /v1/calculate. Throws ApiError on the structured error contract. */
export async function postCalculate(input: CalcInput): Promise<CalcResult> {
  const resp = await fetch(`${BASE_URL}/v1/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (resp.ok) return (await resp.json()) as CalcResult
  const payload = (await resp.json().catch(() => null)) as { error?: ApiErrorBody } | null
  if (payload?.error) throw new ApiError(payload.error)
  throw new Error(`POST /v1/calculate failed: ${resp.status}`)
}
