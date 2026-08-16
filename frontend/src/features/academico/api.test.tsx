import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import * as client from '../../api/client'
import { ApiError } from '../../api/client'
import { useRegistroAsesoresAbierto } from './api'

function envoltura({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('useRegistroAsesoresAbierto', () => {
  afterEach(() => vi.restoreAllMocks())

  it('es true cuando el periodo vigente reporta la ventana abierta', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue({
      semestre: '20271',
      fecha_inicio: '2026-08-10',
      fecha_fin: '2026-12-04',
      registro_asesores_inicio: '2026-07-01',
      registro_asesores_fin: '2026-08-31',
      registro_asesores_abierto: true,
    })
    const { result } = renderHook(() => useRegistroAsesoresAbierto(), { wrapper: envoltura })
    await waitFor(() => expect(result.current).toBe(true))
  })

  it('es false cuando la SAE todavía no dio de alta el periodo (404)', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new ApiError(404, { detail: 'no hay' }))
    const { result } = renderHook(() => useRegistroAsesoresAbierto(), { wrapper: envoltura })
    await waitFor(() => expect(result.current).toBe(false))
  })
})
