import { describe, it, expect, vi, afterEach } from 'vitest'
import { construirRutaMaterias, obtenerTodasLasMaterias, siguientePagina } from './api'
import type { Materia, RespuestaPaginada } from '../../api/types'

const originalFetch = global.fetch

const mockLocalStorage = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', { value: mockLocalStorage, writable: true })

function materia(id: number): Materia {
  return {
    id,
    clave: `000${id}`,
    nombre: `Materia ${id}`,
    carrera: 1,
    nivel: null,
    plan: 2006,
    habilitada_asesorias: true,
  }
}

function respuesta(cuerpo: unknown) {
  return { ok: true, status: 200, json: async () => cuerpo } as Response
}

describe('construirRutaMaterias', () => {
  it('sin parámetros devuelve la ruta desnuda', () => {
    expect(construirRutaMaterias()).toBe('/api/materias/materias/')
  })

  it('omite page=1 porque el backend ya la sirve por defecto', () => {
    expect(construirRutaMaterias({ page: 1 })).toBe('/api/materias/materias/')
  })

  it('serializa habilitada_asesorias como 1 o 0', () => {
    expect(construirRutaMaterias({ habilitada_asesorias: true })).toBe(
      '/api/materias/materias/?habilitada_asesorias=1',
    )
    expect(construirRutaMaterias({ habilitada_asesorias: false })).toBe(
      '/api/materias/materias/?habilitada_asesorias=0',
    )
  })

  it('omite carrera null y search vacío', () => {
    expect(construirRutaMaterias({ carrera: null, search: '' })).toBe('/api/materias/materias/')
  })

  it('combina habilitada_asesorias, carrera, search y page', () => {
    expect(
      construirRutaMaterias({ habilitada_asesorias: true, carrera: 7, search: 'ál ge', page: 3 }),
    ).toBe('/api/materias/materias/?habilitada_asesorias=1&carrera=7&search=%C3%A1l+ge&page=3')
  })
})

describe('obtenerTodasLasMaterias', () => {
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('devuelve el array completo con una sola página', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue(respuesta({ count: 1, next: null, previous: null, results: [materia(1)] }))

    await expect(obtenerTodasLasMaterias()).resolves.toEqual([materia(1)])
  })

  it('recorre todas las páginas hasta que next es null y concatena los resultados', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        respuesta({
          count: 3,
          next: 'http://x/api/materias/materias/?page=2',
          previous: null,
          results: [materia(1)],
        }),
      )
      .mockResolvedValueOnce(
        respuesta({
          count: 3,
          next: 'http://x/api/materias/materias/?page=3',
          previous: 'http://x/api/materias/materias/',
          results: [materia(2)],
        }),
      )
      .mockResolvedValueOnce(
        respuesta({
          count: 3,
          next: null,
          previous: 'http://x/api/materias/materias/?page=2',
          results: [materia(3)],
        }),
      )
    global.fetch = fetchMock

    const materias = await obtenerTodasLasMaterias()

    expect(materias.map((m) => m.id)).toEqual([1, 2, 3])
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/materias/materias/')
    expect(String(fetchMock.mock.calls[1][0])).toContain('page=2')
    expect(String(fetchMock.mock.calls[2][0])).toContain('page=3')
  })

  it('devuelve vacío cuando el catálogo está vacío', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue(respuesta({ count: 0, next: null, previous: null, results: [] }))

    await expect(obtenerTodasLasMaterias()).resolves.toEqual([])
  })
})

describe('siguientePagina', () => {
  function paginaCon(next: string | null): RespuestaPaginada<Materia> {
    return { count: 60, next, previous: null, results: [] }
  }

  it('devuelve undefined cuando next es null, para cortar el scroll infinito', () => {
    const cargadas = [paginaCon(null)]
    expect(siguientePagina(cargadas[0], cargadas)).toBeUndefined()
  })

  it('devuelve el número de páginas ya cargadas + 1', () => {
    const cargadas = [paginaCon('http://x/?page=2'), paginaCon('http://x/?page=3')]
    expect(siguientePagina(cargadas[1], cargadas)).toBe(3)
  })
})
