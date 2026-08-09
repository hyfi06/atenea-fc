import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { OfertaAsesorias } from './OfertaAsesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { MateriaOferta } from '../../../api/types'

const OFERTA: MateriaOferta[] = [
  { materia_id: 1, nombre: 'Álgebra', carrera_id: 3, num_asesores: 2 },
  { materia_id: 2, nombre: 'Cálculo', carrera_id: 3, num_asesores: 1 },
  { materia_id: 3, nombre: 'Física', carrera_id: 9, num_asesores: 1 },
]

function montar() {
  vi.spyOn(api, 'useOferta').mockReturnValue({
    data: OFERTA, isPending: false,
  } as ReturnType<typeof api.useOferta>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(
    new Map([
      [3, { id: 3, nombre: 'Actuaría' } as never],
      [9, { id: 9, nombre: 'Física' } as never],
    ]),
  )
  render(
    <MemoryRouter initialEntries={['/asesorias/nueva']}>
      <Routes>
        <Route path="/asesorias/nueva" element={<OfertaAsesorias />} />
        <Route path="/asesorias/nueva/:materiaId" element={<p>wizard</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('OfertaAsesorias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista las materias con su número de asesores', () => {
    montar()
    expect(screen.getByRole('button', { name: /Álgebra/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Física/ })).toBeInTheDocument()
  })

  it('filtra por búsqueda de nombre', () => {
    montar()
    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'álge' } })
    expect(screen.getByRole('button', { name: /Álgebra/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Cálculo/ })).not.toBeInTheDocument()
  })

  it('navega al wizard al elegir una materia', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Álgebra/ }))
    expect(screen.getByText('wizard')).toBeInTheDocument()
  })
})
