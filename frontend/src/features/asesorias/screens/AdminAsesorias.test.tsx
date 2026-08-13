import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesorias } from './AdminAsesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import * as rol from '../../../auth/rol'
import type { AlumnoBusqueda, AsesorBusqueda, AsesoriaAdmin } from '../../../api/types'

function activarTab(nombre: string) {
  const tab = screen.getByRole('tab', { name: nombre })
  tab.focus()
  fireEvent.keyDown(tab, { key: 'Enter', code: 'Enter' })
  fireEvent.click(tab)
}

const ASESORES: AsesorBusqueda[] = [
  { perfil_id: 7, nombre: 'Ana López', numero_trabajador: '30001' },
]

const ALUMNOS: AlumnoBusqueda[] = [
  { perfil_id: 15, nombre: 'Juan Pérez', numero_cuenta: '312345678' },
]

function asesoria(overrides: Partial<AsesoriaAdmin> = {}): AsesoriaAdmin {
  return {
    id: 1,
    estado: 'agendada',
    fecha: '2026-08-20',
    hora_inicio: '10:00:00',
    materia: 1,
    carrera: 1,
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: '',
    alumno_nombre: 'Juan Pérez',
    asesor_nombre: 'Ana López',
    asistio: null,
    notas: 'trae dudas del examen',
    ...overrides,
  }
}

function montar() {
  vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
  const adminAsesorias = vi.spyOn(api, 'useAdminAsesorias').mockReturnValue({
    data: [asesoria()], isPending: false,
  } as ReturnType<typeof api.useAdminAsesorias>)
  vi.spyOn(api, 'useAdminSemestres').mockReturnValue({
    data: ['20262', '20261'], isPending: false,
  } as ReturnType<typeof api.useAdminSemestres>)
  vi.spyOn(api, 'useBuscarAsesores').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useBuscarAsesores>)
  vi.spyOn(api, 'useBuscarAlumnos').mockReturnValue({
    data: ALUMNOS, isPending: false,
  } as ReturnType<typeof api.useBuscarAlumnos>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )

  render(
    <MemoryRouter initialEntries={['/sae/asesorias']}>
      <Routes>
        <Route path="/sae/asesorias" element={<AdminAsesorias />} />
        <Route path="/sae/asesorias/oferta" element={<p>oferta SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
  return adminAsesorias
}

describe('AdminAsesorias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra los tabs Próximas e Historial', () => {
    montar()
    expect(screen.getByRole('tab', { name: 'Próximas' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Historial' })).toBeInTheDocument()
  })

  it('lista las sesiones con ambos nombres y sin las notas', () => {
    montar()
    expect(screen.getByText(/Juan Pérez · Ana López/)).toBeInTheDocument()
    expect(screen.queryByText(/trae dudas del examen/)).not.toBeInTheDocument()
  })

  it('el historial ofrece un subtab por semestre', () => {
    montar()
    activarTab('Historial')
    expect(screen.getByRole('tab', { name: '20262' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '20261' })).toBeInTheDocument()
  })

  it('elegir un semestre consulta ese semestre', () => {
    const adminAsesorias = montar()
    activarTab('Historial')
    fireEvent.click(screen.getByRole('tab', { name: '20261' }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: null, alumno: null, semestre: '20261' })
  })

  it('buscar y elegir un asesor dispara la consulta con ese asesor', () => {
    const adminAsesorias = montar()
    fireEvent.change(screen.getByLabelText('Asesor'), { target: { value: 'ana' } })
    // Acotado a la lista de resultados: la tarjeta admin también es un botón
    // y su nombre accesible incluye "Ana López".
    const resultados = screen.getByRole('list', { name: 'Resultados de asesores' })
    fireEvent.click(within(resultados).getByRole('button', { name: /Ana López/ }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: 7, alumno: null })
  })

  it('el filtro de alumno dispara la consulta con ese alumno', () => {
    const adminAsesorias = montar()
    fireEvent.change(screen.getByLabelText('Alumno'), { target: { value: 'jua' } })
    const resultados = screen.getByRole('list', { name: 'Resultados de alumnos' })
    fireEvent.click(within(resultados).getByRole('button', { name: /Juan Pérez/ }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: null, alumno: 15 })
  })

  it('navega a la consulta de oferta', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Consultar oferta' }))
    expect(screen.getByText('oferta SAE')).toBeInTheDocument()
  })
})
