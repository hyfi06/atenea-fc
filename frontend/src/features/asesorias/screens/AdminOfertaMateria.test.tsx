import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminOfertaMateria } from './AdminOfertaMateria'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
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

function montar() {
  vi.spyOn(api, 'useAsesoresDeMateria').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAsesoresDeMateria>)
  vi.spyOn(api, 'useDisponibilidadDeAsesor').mockReturnValue({
    data: SLOTS, isPending: false,
  } as ReturnType<typeof api.useDisponibilidadDeAsesor>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[12, { id: 12, nombre: 'Álgebra' } as never]]),
  )

  render(
    <MemoryRouter initialEntries={['/sae/asesorias/oferta/12']}>
      <Routes>
        <Route path="/sae/asesorias/oferta/:materiaId" element={<AdminOfertaMateria />} />
        <Route path="/sae/asesorias/oferta" element={<p>oferta SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminOfertaMateria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra la materia y sus asesores', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Álgebra' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ana López/ })).toBeInTheDocument()
  })

  it('al elegir un asesor muestra su disponibilidad por día', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.getByText('Disponibilidad')).toBeInTheDocument()
    expect(screen.getByText(/10:00–10:30/)).toBeInTheDocument()
  })

  it('no ofrece agendar ni selector de carrera', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.queryByRole('button', { name: /Agendar/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Carrera')).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('los bloques de disponibilidad no son interactivos', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.queryByRole('button', { name: /10:00–10:30/ })).not.toBeInTheDocument()
  })

  it('vuelve a la oferta', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Volver a la oferta' }))
    expect(screen.getByText('oferta SAE')).toBeInTheDocument()
  })
})
