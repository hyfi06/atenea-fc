import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AgendarAsesoria } from './AgendarAsesoria'
import * as api from '../api'
import * as auth from '../../../auth/AuthContext'
import * as catalogo from '../../catalogo/api'
import { ApiError } from '../../../api/client'
import type { AsesorDisponible, SlotDisponibilidad } from '../../../api/types'

const ASESORES: AsesorDisponible[] = [
  { registro_id: 7, asesor_nombre: 'Ana López', area_nombre: 'Matemáticas', formatos: ['virtual'] },
]
const SLOTS: SlotDisponibilidad[] = [
  {
    registro_id: 7, asesor_nombre: 'Ana López', disponibilidad_id: 41, fecha: '2026-08-10',
    hora_inicio: '10:00:00', hora_fin: '10:30:00', formato: 'virtual', ubicacion: '', liga_virtual: 'https://x',
  },
]

function mockComun(mutateImpl: ReturnType<typeof vi.fn>) {
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
    user: { perfil_alumno: { id: 1, carrera: 3, carrera_nombre: 'Actuaría' } },
    status: 'authenticated',
  } as unknown as ReturnType<typeof auth.useAuth>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(new Map([[3, { id: 3, nombre: 'Actuaría' } as never]]))
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
