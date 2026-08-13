import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MisMaterias } from './MisMaterias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { Materia, RegistroAsesor } from '../../../api/types'

const NOMBRE_LARGO = 'Aplicación de las Ciencias de la Tierra en la Vigilancia de Ensayos Nucleares'

const REGISTRO: RegistroAsesor = { id: 3, semestre: '20262', materias: [1, 2] }

function materia(id: number, nombre: string): Materia {
  return { id, clave: `000${id}`, nombre, carrera: 1, nivel: null, plan: 1, habilitada_asesorias: true }
}

function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

function montar() {
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: REGISTRO, cargando: false })
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([
      [1, materia(1, NOMBRE_LARGO)],
      [2, materia(2, 'Física')],
    ]),
  )
  const quitar = vi.fn()
  vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
    mutate: quitar,
    isPending: false,
  } as unknown as ReturnType<typeof api.useQuitarMateria>)
  vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof api.useAgregarMateria>)

  render(<MisMaterias />, { wrapper: envolver })
  return quitar
}

describe('MisMaterias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista las materias del registro con el nombre completo en title', () => {
    montar()

    const fila = screen.getByRole('button', { name: NOMBRE_LARGO })
    expect(fila).toHaveAttribute('title', NOMBRE_LARGO)
    expect(fila).toHaveClass('truncate')
  })

  it('al tocar la fila deja de truncar, para que el nombre completo sea accesible en móvil', () => {
    montar()

    const fila = screen.getByRole('button', { name: NOMBRE_LARGO })
    fireEvent.click(fila)

    expect(fila).not.toHaveClass('truncate')
  })

  it('quitar pide confirmación con el copy de la spec y luego llama al endpoint', () => {
    const quitar = montar()

    fireEvent.click(screen.getByRole('button', { name: 'Quitar Física' }))

    expect(
      screen.getByText(
        'Ya no aparecerás como asesor de esta materia en búsquedas de alumnos. Las asesorías ya agendadas no se cancelan.',
      ),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('button').map((b) => b.textContent)).toContain('Quitar')

    fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))

    expect(quitar).toHaveBeenCalledWith(2, expect.anything())
  })

  it('sin materias muestra el estado vacío', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({
      registro: { ...REGISTRO, materias: [] },
      cargando: false,
    })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map())
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias />, { wrapper: envolver })

    expect(screen.getByText('Todavía no impartes ninguna materia este semestre.')).toBeInTheDocument()
  })

  it('en solo lectura muestra las materias recibidas y el semestre pedido', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[2, materia(2, 'Física')]]))
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias soloLectura materias={[2]} semestre="20261" />, { wrapper: envolver })

    expect(screen.getByRole('button', { name: 'Física' })).toBeInTheDocument()
    expect(screen.getByText('Semestre 20261')).toBeInTheDocument()
  })

  it('en solo lectura no ofrece agregar ni quitar', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[2, materia(2, 'Física')]]))
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias soloLectura materias={[2]} semestre="20261" />, { wrapper: envolver })

    expect(screen.queryByRole('button', { name: '+ Agregar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar Física' })).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('en solo lectura sin materias muestra el vacío del asesor consultado', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map())
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias soloLectura materias={[]} semestre="20261" />, { wrapper: envolver })

    expect(
      screen.getByText('Este asesor no imparte materias en el semestre seleccionado.'),
    ).toBeInTheDocument()
  })
})
