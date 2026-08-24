import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { DialogoAgregarMateria } from './DialogoAgregarMateria'
import * as catalogo from '../../catalogo/api'
import type { Carrera, Materia, RespuestaPaginada } from '../../../api/types'

let disparaInterseccion: (() => void) | null = null

class ObservadorEspia {
  constructor(callback: IntersectionObserverCallback) {
    disparaInterseccion = () =>
      callback(
        [{ isIntersecting: true } as IntersectionObserverEntry],
        this as unknown as IntersectionObserver,
      )
  }
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

function crearMateria(overrides: Partial<Materia>): Materia {
  return {
    id: 1, clave: '0001', nombre: 'Cálculo I', carrera: 1, nivel: null,
    plan: 1, habilitada_asesorias: true, ...overrides,
  }
}

function crearCarrera(id: number, nombre: string): Carrera {
  return { id, clave: 800 + id, nombre, area: { id: 1, nombre: 'Área' }, acepta_nuevo_ingreso: true }
}

function pagina(results: Materia[], next: string | null): RespuestaPaginada<Materia> {
  return { count: results.length, next, previous: null, results }
}

interface OpcionesMontaje {
  paginas?: RespuestaPaginada<Materia>[]
  hasNextPage?: boolean
  isFetchingNextPage?: boolean
  carreras?: Carrera[]
}

function montar(opciones: OpcionesMontaje = {}) {
  const {
    paginas = [pagina([crearMateria({ id: 1, nombre: 'Cálculo I' })], null)],
    hasNextPage = false,
    isFetchingNextPage = false,
    carreras = [crearCarrera(1, 'Matemáticas'), crearCarrera(2, 'Física')],
  } = opciones

  disparaInterseccion = null
  globalThis.IntersectionObserver = ObservadorEspia as unknown as typeof IntersectionObserver

  const fetchNextPage = vi.fn()
  const usarInfinitas = vi.spyOn(catalogo, 'useMateriasInfinitas').mockReturnValue({
    data: { pages: paginas, pageParams: paginas.map((_, i) => i + 1) },
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } as unknown as ReturnType<typeof catalogo.useMateriasInfinitas>)
  vi.spyOn(catalogo, 'useCarreras').mockReturnValue({
    data: carreras,
  } as ReturnType<typeof catalogo.useCarreras>)

  const onConfirmar = vi.fn()
  render(
    <DialogoAgregarMateria abierto cargando={false} error={null} onConfirmar={onConfirmar} onCerrar={vi.fn()} />,
  )
  return { onConfirmar, fetchNextPage, usarInfinitas }
}

describe('DialogoAgregarMateria', () => {
  afterEach(() => {
    disparaInterseccion = null
    vi.restoreAllMocks()
  })

  it('pide al backend solo las materias habilitadas para asesorías', () => {
    const { usarInfinitas } = montar()

    expect(usarInfinitas).toHaveBeenCalledWith({
      habilitada_asesorias: true,
      carrera: null,
      search: '',
    })
  })

  it('lista las materias de todas las páginas cargadas', () => {
    montar({
      paginas: [
        pagina([crearMateria({ id: 1, nombre: 'Cálculo I' })], 'http://x/?page=2'),
        pagina([crearMateria({ id: 2, nombre: 'Física' })], null),
      ],
    })

    expect(screen.getByRole('button', { name: 'Cálculo I' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Física' })).toBeInTheDocument()
  })

  it('manda la búsqueda al backend con debounce, sin filtrar en cliente', async () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'fís' } })

    expect(usarInfinitas).not.toHaveBeenCalledWith(
      expect.objectContaining({ search: 'fís' }),
    )
    await waitFor(
      () =>
        expect(usarInfinitas).toHaveBeenCalledWith({
          habilitada_asesorias: true,
          carrera: null,
          search: 'fís',
        }),
      { timeout: 2000 },
    )
  })

  it('cambiar de carrera dispara la query con el filtro, sin esperar el debounce', () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '2' } })

    expect(usarInfinitas).toHaveBeenCalledWith({
      habilitada_asesorias: true,
      carrera: 2,
      search: '',
    })
  })

  it('combina carrera y búsqueda en la misma query', async () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'ondas' } })

    await waitFor(
      () =>
        expect(usarInfinitas).toHaveBeenCalledWith({
          habilitada_asesorias: true,
          carrera: 2,
          search: 'ondas',
        }),
      { timeout: 2000 },
    )
  })

  it('vuelve a Todas las carreras al elegir la opción vacía', () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '' } })

    expect(usarInfinitas).toHaveBeenLastCalledWith({
      habilitada_asesorias: true,
      carrera: null,
      search: '',
    })
  })

  it('puebla el selector con el catálogo completo de carreras', () => {
    montar()

    expect(screen.getByRole('option', { name: 'Todas' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Matemáticas' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Física' })).toBeInTheDocument()
  })

  it('al llegar el sentinela a la vista pide la siguiente página', () => {
    const { fetchNextPage } = montar({ hasNextPage: true })

    expect(disparaInterseccion).not.toBeNull()
    act(() => disparaInterseccion?.())

    expect(fetchNextPage).toHaveBeenCalled()
  })

  it('no observa nada cuando ya no hay más páginas', () => {
    montar({ hasNextPage: false })

    expect(disparaInterseccion).toBeNull()
  })

  it('avisa mientras carga la siguiente página', () => {
    montar({ hasNextPage: true, isFetchingNextPage: true })

    expect(screen.getByText('Cargando más…')).toBeInTheDocument()
  })

  it('mantiene Agregar deshabilitado hasta que hay una materia seleccionada', () => {
    const { onConfirmar } = montar({
      paginas: [pagina([crearMateria({ id: 7, nombre: 'Física' })], null)],
    })

    expect(screen.getByRole('button', { name: 'Agregar' })).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Física' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }))

    expect(onConfirmar).toHaveBeenCalledWith(7)
  })
})
