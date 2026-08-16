import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AgendarAsesoria } from './AgendarAsesoria'
import * as api from '../api'
import * as auth from '../../../auth/AuthContext'
import * as catalogo from '../../catalogo/api'
import { ApiError } from '../../../api/client'
import type { AsesorDisponible, SlotDisponibilidad, InscripcionAlumno } from '../../../api/types'

const ASESORES: AsesorDisponible[] = [
  { registro_id: 7, asesor_nombre: 'Ana López', area_nombre: 'Matemáticas', formatos: ['virtual'] },
]
const SLOTS: SlotDisponibilidad[] = [
  {
    registro_id: 7, asesor_nombre: 'Ana López', disponibilidad_id: 41, fecha: '2026-08-10',
    hora_inicio: '10:00:00', hora_fin: '10:30:00', formato: 'virtual', ubicacion: '', liga_virtual: 'https://x',
  },
]

const HISTORIAL_UNA: InscripcionAlumno[] = [
  { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
]

function mockComun(
  mutateImpl: ReturnType<typeof vi.fn>,
  historial: InscripcionAlumno[] = HISTORIAL_UNA,
) {
  vi.spyOn(api, 'useAsesoresDeMateria').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAsesoresDeMateria>)
  vi.spyOn(api, 'useDisponibilidadDeAsesor').mockReturnValue({
    data: SLOTS, isPending: false,
  } as ReturnType<typeof api.useDisponibilidadDeAsesor>)
  vi.spyOn(api, 'useAgendarAsesoria').mockReturnValue({
    mutate: mutateImpl, isPending: false,
  } as unknown as ReturnType<typeof api.useAgendarAsesoria>)
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: { perfil_alumno: { id: 1, numero_cuenta: '312345678', historial } },
    status: 'authenticated',
  } as unknown as ReturnType<typeof auth.useAuth>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(
    new Map([
      [3, { id: 3, nombre: 'Actuaría' } as never],
      [6, { id: 6, nombre: 'Matemáticas' } as never],
    ]),
  )
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[12, { id: 12, nombre: 'Álgebra' } as never]]))
}

function montar(entrada = '/asesorias/nueva/12') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entrada]}>
        <Routes>
          <Route path="/asesorias/nueva/:materiaId" element={<AgendarAsesoria />} />
          <Route path="/asesorias" element={<p>lista de asesorías</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return queryClient
}

function avanzarHastaConfirmar() {
  fireEvent.click(screen.getByText('Ana López'))
  fireEvent.click(screen.getByText(/10 de agosto/i))
  fireEvent.click(screen.getByText('10:00–10:30'))
  // Botón que abre el diálogo (etiqueta distinta a la acción del diálogo).
  fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
}

describe('AgendarAsesoria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('elegir asesor avanza al paso de día', () => {
    mockComun(vi.fn())
    montar()
    fireEvent.click(screen.getByText('Ana López'))
    expect(screen.getByText('Elige un día')).toBeInTheDocument()
  })

  it('confirmar dispara el POST con el payload correcto', () => {
    const mutate = vi.fn()
    mockComun(mutate)
    montar()
    avanzarHastaConfirmar()
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' })) // botón del diálogo
    expect(mutate).toHaveBeenCalledWith(
      { disponibilidad: 41, fecha: '2026-08-10', materia: 12, carrera: 3 },
      expect.anything(),
    )
  })

  it('un 409 regresa al paso de día', async () => {
    const mutate = vi.fn((_payload, { onError }) => onError(new ApiError(409, { detail: 'tomado' })))
    mockComun(mutate)
    montar()
    avanzarHastaConfirmar()
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(await screen.findByText('Elige un día')).toBeInTheDocument()
    expect(screen.getByText(/ya fue tomado/i)).toBeInTheDocument()
  })

  it('un 409 invalida la búsqueda de disponibilidad para forzar el refetch', () => {
    const mutate = vi.fn((_payload, { onError }) => onError(new ApiError(409, { detail: 'tomado' })))
    mockComun(mutate)
    const queryClient = montar()
    const invalidar = vi.spyOn(queryClient, 'invalidateQueries')
    avanzarHastaConfirmar()
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(invalidar).toHaveBeenCalledWith({ queryKey: ['disponibilidad'] })
  })

  it('un usuario sin perfil de alumno no puede agendar', () => {
    mockComun(vi.fn())
    vi.spyOn(auth, 'useAuth').mockReturnValue({
      user: { perfil_alumno: null },
      status: 'authenticated',
    } as unknown as ReturnType<typeof auth.useAuth>)
    montar()
    expect(screen.getByText(/sólo los alumnos pueden agendar/i)).toBeInTheDocument()
    expect(screen.queryByText('Ana López')).not.toBeInTheDocument()
  })
})

describe('AgendarAsesoria — selección de carrera', () => {
  afterEach(() => vi.restoreAllMocks())

  function avanzarHastaCarrera() {
    fireEvent.click(screen.getByText('Ana López'))
    fireEvent.click(screen.getByText(/10 de agosto/i))
    fireEvent.click(screen.getByText('10:00–10:30'))
  }

  it('con una sola inscripción deja la carrera preseleccionada', () => {
    mockComun(vi.fn())
    montar()
    avanzarHastaCarrera()
    expect((screen.getByLabelText('Carrera') as HTMLSelectElement).value).toBe('3')
  })

  it('con dos inscripciones ofrece ambas y no preselecciona ninguna', () => {
    mockComun(vi.fn(), [
      { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
      { carrera: 6, carrera_nombre: 'Matemáticas', generacion: 2025 },
    ])
    montar()
    avanzarHastaCarrera()
    const select = screen.getByLabelText('Carrera') as HTMLSelectElement
    expect(select.value).toBe('')
    expect([...select.options].map((o) => o.textContent)).toEqual([
      'Elige una carrera', 'Actuaría', 'Matemáticas',
    ])
  })

  it('con dos inscripciones el POST manda la que se eligió', () => {
    const mutate = vi.fn()
    mockComun(mutate, [
      { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
      { carrera: 6, carrera_nombre: 'Matemáticas', generacion: 2025 },
    ])
    montar()
    avanzarHastaCarrera()
    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '6' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ carrera: 6 }),
      expect.anything(),
    )
  })
})
