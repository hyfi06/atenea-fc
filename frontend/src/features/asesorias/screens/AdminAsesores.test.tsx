import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesores } from './AdminAsesores'
import * as api from '../api'
import type { AsesorDirectorio } from '../../../api/types'

const ASESORES: AsesorDirectorio[] = [
  { perfil_id: 7, nombre: 'Ana López', numero_trabajador: '30001', area_nombre: 'Matemáticas', activo: true, num_materias_semestre_vigente: 3 },
  { perfil_id: 9, nombre: 'Luis Ruiz', numero_trabajador: '30002', area_nombre: 'Física', activo: false, num_materias_semestre_vigente: 1 },
]

function montar() {
  vi.spyOn(api, 'useAdminAsesores').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAdminAsesores>)

  render(
    <MemoryRouter initialEntries={['/sae/asesores']}>
      <Routes>
        <Route path="/sae/asesores" element={<AdminAsesores />} />
        <Route path="/sae/asesores/:asesorId" element={<p>detalle de asesor</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminAsesores', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista los asesores con área, estado y número de materias', () => {
    montar()
    expect(screen.getByRole('button', { name: /Ana López/ })).toBeInTheDocument()
    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    expect(screen.getByText('Activo')).toBeInTheDocument()
    expect(screen.getByText('Inactivo')).toBeInTheDocument()
    expect(screen.getByText('3 materias')).toBeInTheDocument()
    expect(screen.getByText('1 materia')).toBeInTheDocument()
  })

  it('filtra por nombre en el cliente', () => {
    montar()
    fireEvent.change(screen.getByLabelText('Buscar asesor'), { target: { value: 'luis' } })
    expect(screen.getByRole('button', { name: /Luis Ruiz/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Ana López/ })).not.toBeInTheDocument()
  })

  it('navega al detalle del asesor elegido', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.getByText('detalle de asesor')).toBeInTheDocument()
  })

  it('sin coincidencias muestra el estado vacío de la búsqueda', () => {
    montar()
    fireEvent.change(screen.getByLabelText('Buscar asesor'), { target: { value: 'zzz' } })
    expect(screen.getByText('Ningún asesor coincide con tu búsqueda.')).toBeInTheDocument()
  })
})
