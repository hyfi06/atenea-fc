import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminDetalleAsesoria } from './AdminDetalleAsesoria'
import type { AsesoriaAdmin } from '../../../api/types'

function asesoria(overrides: Partial<AsesoriaAdmin> = {}): AsesoriaAdmin {
  return {
    id: 1,
    estado: 'realizada',
    fecha: '2026-08-20',
    hora_inicio: '10:00:00',
    materia: 1,
    carrera: 1,
    formato: 'presencial',
    ubicacion: 'Salón 4',
    liga_virtual: '',
    alumno_nombre: 'Juan Pérez',
    asesor_nombre: 'Ana López',
    asistio: true,
    notas: 'trae dudas del examen',
    ...overrides,
  }
}

/** La pantalla se alimenta sólo del router state; `MemoryRouter` acepta
 *  entradas como objeto `Location`, así que el state se inyecta ahí. */
function montar(state: unknown = { asesoria: asesoria(), nombreMateria: 'Cálculo I' }) {
  render(
    <MemoryRouter initialEntries={[{ pathname: '/sae/asesorias/1', state }]}>
      <Routes>
        <Route path="/sae/asesorias/:id" element={<AdminDetalleAsesoria />} />
        <Route path="/sae/asesorias" element={<p>lista SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminDetalleAsesoria', () => {
  it('muestra la materia, el estado y ambos nombres', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Cálculo I' })).toBeInTheDocument()
    expect(screen.getByText('Realizada')).toBeInTheDocument()
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('Ana López')).toBeInTheDocument()
  })

  it('muestra las notas de la sesión', () => {
    montar()
    expect(screen.getByText('Notas de la sesión')).toBeInTheDocument()
    expect(screen.getByText('trae dudas del examen')).toBeInTheDocument()
  })

  it('sin notas no muestra la sección de notas', () => {
    montar({ asesoria: asesoria({ notas: '   ' }), nombreMateria: 'Cálculo I' })
    expect(screen.queryByText('Notas de la sesión')).not.toBeInTheDocument()
  })

  it('no ofrece ninguna acción de escritura', () => {
    montar()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Guardar/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Cancelar/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /asistió/i })).not.toBeInTheDocument()
  })

  it('la sesión presencial muestra la ubicación', () => {
    montar()
    expect(screen.getByText('Salón 4')).toBeInTheDocument()
  })

  it('la sesión virtual muestra la liga', () => {
    montar({
      asesoria: asesoria({ formato: 'virtual', ubicacion: '', liga_virtual: 'https://meet.example.com/x' }),
      nombreMateria: 'Cálculo I',
    })
    expect(screen.getByRole('link', { name: 'Liga de la sesión' })).toHaveAttribute(
      'href',
      'https://meet.example.com/x',
    )
  })

  it('sin router state (deep-link o refresh) muestra el estado vacío', () => {
    montar(null)
    expect(screen.getByText(/No se encontró la asesoría/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Volver a Asesorías SAE/ })).toBeInTheDocument()
  })

  it('sin nombre de materia en el state cae al identificador', () => {
    montar({ asesoria: asesoria() })
    expect(screen.getByRole('heading', { name: 'Materia #1' })).toBeInTheDocument()
  })

  it('el botón volver regresa a la lista SAE', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Volver a Asesorías SAE/ }))
    expect(screen.getByText('lista SAE')).toBeInTheDocument()
  })
})
