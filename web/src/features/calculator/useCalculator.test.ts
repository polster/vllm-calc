import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { CalcResult } from '../../api/types.ts'
import type { CalculatorDeps } from './useCalculator.ts'
import { useCalculator } from './useCalculator.ts'

function makeResult(overrides: Partial<CalcResult> = {}): CalcResult {
  return {
    fits: true,
    requested_max_seqs: 32,
    max_concurrent: 42,
    verdict: 'Fits — supports up to 42.',
    worst_case_note: 'conservative',
    supported_vllm_range: '>=0.13,<0.14',
    warnings: [],
    serve_command: 'vllm serve <your-model> --tensor-parallel-size 2',
    breakdown: {
      weights_per_gpu_bytes: 1,
      kv_per_gpu_bytes: 1,
      overhead_fixed_context_bytes: 1,
      overhead_activations_bytes: 1,
      overhead_cuda_graphs_bytes: 1,
      overhead_total_bytes: 1,
      used_per_gpu_bytes: 1,
      budget_per_gpu_bytes: 1,
      available_for_kv_bytes: 1,
    },
    ...overrides,
  }
}

function makeDeps(overrides: Partial<CalculatorDeps> = {}): CalculatorDeps {
  return {
    calculate: vi.fn().mockResolvedValue(makeResult()),
    fetchModels: vi.fn().mockResolvedValue([]),
    fetchGpus: vi.fn().mockResolvedValue([]),
    ...overrides,
  }
}

describe('useCalculator', () => {
  it('computes the default scenario on load', async () => {
    const deps = makeDeps()
    const { result } = renderHook(() => useCalculator(deps))

    expect(result.current.status).toBe('loading')
    await waitFor(() => expect(result.current.status).toBe('ready'))
    expect(result.current.result?.max_concurrent).toBe(42)
    expect(deps.calculate).toHaveBeenCalledTimes(1)
  })

  it('recomputes when input changes', async () => {
    const deps = makeDeps()
    const { result } = renderHook(() => useCalculator(deps))
    await waitFor(() => expect(result.current.status).toBe('ready'))

    act(() => result.current.setInput({ ctx_len: 4096 }))
    await waitFor(() => expect(deps.calculate).toHaveBeenCalledTimes(2))
    expect((deps.calculate as ReturnType<typeof vi.fn>).mock.calls[1][0].ctx_len).toBe(4096)
  })

  it('keeps the last valid result when a recompute errors', async () => {
    const calculate = vi
      .fn()
      .mockResolvedValueOnce(makeResult({ max_concurrent: 42 }))
      .mockRejectedValueOnce(new Error("TP must divide the model's attention heads"))
    const { result } = renderHook(() => useCalculator(makeDeps({ calculate })))
    await waitFor(() => expect(result.current.status).toBe('ready'))

    act(() => result.current.setInput({ tensor_parallel_size: 3 }))
    await waitFor(() => expect(result.current.status).toBe('error'))
    expect(result.current.error).toMatch(/attention heads/)
    expect(result.current.result?.max_concurrent).toBe(42) // last valid result persists
  })

  it('loads presets on mount', async () => {
    const deps = makeDeps({
      fetchModels: vi.fn().mockResolvedValue([{ id: 'llama-3.3-70b' }]),
    })
    const { result } = renderHook(() => useCalculator(deps))
    await waitFor(() => expect(result.current.modelPresets).toHaveLength(1))
  })
})
