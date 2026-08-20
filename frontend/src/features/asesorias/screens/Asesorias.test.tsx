import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Asesorias } from './Asesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

function crearAsesoria(overrides: Partial<Asesoria> = {}): Asesoria {
  return {
    id: 1, alumno: 10, alumno_nombre: 'Beto', asesor_nombre: 'Ana',
    disponibilidad: 1, materia: 1, carrera: 1, fecha: '2026-08-03', hora_inicio: '10:00:00',
    formato: 'virtual', ubicacion: '', liga_virtual: '', estado: 'agendada', asistio: null,
    notas: '', creado_en: '2026-08-01T10:00:00Z', ...overrides,
  }
}

function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[{ pathname: '/asesorias', state: estadoInicial }]}>
        <Routes>
          <Route path="/asesorias" element={children} />
          <Route path="/home" element={<p>pantalla home</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

let estadoInicial: unknown = null

function montar({
  esAsesor,
  esAlumno,
  asesorActivo = true,
  state = null,
  historial = [],
}: {
  esAsesor: boolean
  esAlumno: boolean
  asesorActivo?: boolean
  state?: unknown
  historial?: Asesoria[]
}) {
  estadoInicial = state
  // jsdom no implementa scrollIntoView y `destacar` lo invoca.
  Element.prototype.scrollIntoView = vi.fn()
  vi.spyOn(rol, 'useEsAsesor').mockReturnValue(esAsesor)
  vi.spyOn(rol, 'useEsAlumno').mockReturnValue(esAlumno)
  vi.spyOn(rol, 'useEsAcademico').mockReturnValue(false)
  vi.spyOn(rol, 'useAsesorActivo').mockReturnValue(asesorActivo)
  vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
    data: [crearAsesoria({ id: 1 })], isPending: false,
  } as ReturnType<typeof api.useMisAsesorias>)
  vi.spyOn(api, 'useSemestres').mockReturnValue({
    data: historial.length > 0 ? ['20262'] : [], isPending: false,
  } as ReturnType<typeof api.useSemestres>)
  vi.spyOn(api, 'useAsesoriasDeSemestre').mockReturnValue({
    data: historial, isPending: false,
  } as ReturnType<typeof api.useAsesoriasDeSemestre>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )
  render(<Asesorias />, { wrapper: envolver })
}

describe('Asesorias (vista unificada)', () => {
  afterEach(() => vi.restoreAllMocks())

  it('el alumno ve Nueva asesoría y no las acciones del asesor', () => {
    montar({ esAsesor: false, esAlumno: true })
    expect(screen.getByRole('button', { name: 'Nueva asesoría' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mis materias' })).not.toBeInTheDocument()
  })

  it('el asesor ve Mis materias / Mi horario y no Nueva asesoría', () => {
    montar({ esAsesor: true, esAlumno: false })
    expect(screen.getByRole('button', { name: 'Mis materias' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mi horario' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Nueva asesoría' })).not.toBeInTheDocument()
  })

  it('muestra las tabs Próximas e Historial para ambos', () => {
    montar({ esAsesor: false, esAlumno: true })
    expect(screen.getByRole('tab', { name: 'Próximas' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Historial' })).toBeInTheDocument()
  })

  it('ofrece volver a Inicio', () => {
    montar({ esAsesor: false, esAlumno: true })
    fireEvent.click(screen.getByRole('button', { name: '← Inicio' }))
    expect(screen.getByText('pantalla home')).toBeInTheDocument()
  })

  it('el asesor pendiente no ve Mis materias / Mi horario sino el aviso de revisión', () => {
    montar({ esAsesor: true, esAlumno: false, asesorActivo: false })
    expect(screen.queryByRole('button', { name: 'Mis materias' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mi horario' })).not.toBeInTheDocument()
    expect(screen.getByText('Tu perfil de asesor está pendiente de revisión de la SAE.')).toBeInTheDocument()
  })

  it('al llegar con historialDestacarId abre la pestaña Historial', () => {
    montar({
      esAsesor: true,
      esAlumno: false,
      state: { historialDestacarId: 7 },
      historial: [crearAsesoria({ id: 7, estado: 'realizada', fecha: '2020-01-01' })],
    })
    expect(screen.getByRole('tab', { name: 'Historial' })).toHaveAttribute('aria-selected', 'true')
  })

  it('destaca en Historial la sesión que viene en el router state', () => {
    montar({
      esAsesor: true,
      esAlumno: false,
      state: { historialDestacarId: 7 },
      historial: [crearAsesoria({ id: 7, estado: 'realizada', fecha: '2020-01-01' })],
    })
    expect(screen.getByRole('button', { name: /Cálculo I/ })).toHaveClass('pulso-exito')
  })
})
