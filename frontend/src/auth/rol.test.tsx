import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEsAsesor } from './rol'
import * as client from '../api/client'

function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

describe('useEsAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('resuelve true si GET /api/asesorias/registros/ responde ok', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue([])
    const { result } = renderHook(() => useEsAsesor(), { wrapper: envolver })
    await waitFor(() => expect(result.current.data).toBe(true))
  })

  it('resuelve false si el endpoint responde 403', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(403, { message: 'Se requiere un perfil de asesor académico.' }))
    const { result } = renderHook(() => useEsAsesor(), { wrapper: envolver })
    await waitFor(() => expect(result.current.data).toBe(false))
  })
})
