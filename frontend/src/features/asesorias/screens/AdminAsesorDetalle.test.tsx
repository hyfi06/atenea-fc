import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesorDetalle } from './AdminAsesorDetalle'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { AsesorDetalle } from '../../../api/types'

const DETALLE: AsesorDetalle = {
  perfil_id: 7,
  nombre: 'Ana López',
  area_nombre: 'Matemáticas',
  activo: true,
  semestre: '20262',
  materias: [{ id: 12, clave: '1234', nombre: 'Cálculo III' }],
  disponibilidades: [
    {
      id: 41,
      dia_semana: 0,
      hora_inicio: '09:00:00',
      formato: 'presencial',
      ubicacion: 'Salón O-221',
      liga_virtual: '',
      activa: true,
    },
  ],
}

function montar() {
  const adminAsesor = vi.spyOn(api, 'useAdminAsesor').mockReturnValue({
    data: DETALLE, isPending: false,
  } as ReturnType<typeof api.useAdminAsesor>)
  vi.spyOn(api, 'useAdminSemestres').mockReturnValue({
    data: ['20262', '20261'], isPending: false,
  } as ReturnType<typeof api.useAdminSemestres>)
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
  vi.spyOn(api, 'useMisDisponibilidades').mockReturnValue({
    data: [], isPending: false,
  } as ReturnType<typeof api.useMisDisponibilidades>)
  vi.spyOn(api, 'useSesionesFuturas').mockReturnValue({
    data: { total: 0, sesiones: [] }, isPending: false,
  } as ReturnType<typeof api.useSesionesFuturas>)
  vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useAgregarMateria>)
  vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useQuitarMateria>)
  vi.spyOn(api, 'useCrearDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useCrearDisponibilidad>)
  vi.spyOn(api, 'useActualizarDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useActualizarDisponibilidad>)
  vi.spyOn(api, 'useEliminarDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useEliminarDisponibilidad>)
  vi.spyOn(api, 'useDesactivarDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useDesactivarDisponibilidad>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[12, { id: 12, nombre: 'Cálculo III' } as never]]),
  )

  render(
    <MemoryRouter initialEntries={['/sae/asesores/7']}>
      <Routes>
        <Route path="/sae/asesores/:asesorId" element={<AdminAsesorDetalle />} />
        <Route path="/sae/asesores" element={<p>directorio</p>} />
      </Routes>
    </MemoryRouter>,
  )
  return adminAsesor
}

describe('AdminAsesorDetalle', () => {
  beforeEach(() => {
    // Lunes: la pestaña por default del horario es la del bloque de prueba.
    vi.setSystemTime(new Date('2026-08-03T10:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('muestra la identidad del asesor', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Ana López' })).toBeInTheDocument()
    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    // aria-label propio: el texto "Activo" también aparece en la leyenda y en
    // los chips de la rejilla de horario.
    expect(screen.getByLabelText('Asesor activo')).toBeInTheDocument()
  })

  it('reusa materias y horario en modo solo lectura', () => {
    montar()
    expect(screen.getByRole('button', { name: 'Cálculo III' })).toBeInTheDocument()
    expect(screen.getByText('Semestre 20262')).toBeInTheDocument()
    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })

  it('no ofrece ninguna acción de escritura', () => {
    montar()
    expect(screen.queryByRole('button', { name: '+ Agregar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar Cálculo III' })).not.toBeInTheDocument()
    expect(screen.queryAllByRole('button', { name: /^Horario/ })).toHaveLength(0)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cambiar de semestre recarga el detalle con ese semestre', () => {
    const adminAsesor = montar()
    fireEvent.change(screen.getByLabelText('Semestre'), { target: { value: '20261' } })
    expect(adminAsesor).toHaveBeenCalledWith(7, '20261')
  })

  it('vuelve al directorio', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Volver al directorio' }))
    expect(screen.getByText('directorio')).toBeInTheDocument()
  })
})
