import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiGet, apiPost, ApiError } from './client'

const originalFetch = global.fetch

// Mock localStorage for Node environment
const mockLocalStorage = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
})

describe('apiGet', () => {
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('lanza ApiError con status y body cuando la respuesta no es ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'No puedes operar sobre una sesión ajena.' }),
    } as Response)

    await expect(apiGet('/api/asesorias/asesorias/1/')).rejects.toMatchObject({
      status: 403,
      body: { detail: 'No puedes operar sobre una sesión ajena.' },
    })
  })

  it('devuelve el JSON parseado cuando la respuesta es ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 1 }),
    } as Response)

    await expect(apiGet<{ id: number }>('/api/materias/materias/1/')).resolves.toEqual({ id: 1 })
  })
})

describe('apiPost', () => {
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('manda el body como JSON con Content-Type', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    } as Response)
    global.fetch = fetchMock

    await apiPost('/api/asesorias/asesorias/1/cancelar/', { motivo: 'ya no puedo' })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ motivo: 'ya no puedo' }))
    expect(init.credentials).toBe('include')
  })
})
