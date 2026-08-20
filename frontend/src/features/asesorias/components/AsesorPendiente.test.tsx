import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AsesorPendiente } from './AsesorPendiente'

function montar(titulo = 'Mis materias') {
  render(
    <MemoryRouter initialEntries={['/asesorias/materias']}>
      <Routes>
        <Route path="/asesorias/materias" element={<AsesorPendiente titulo={titulo} />} />
        <Route path="/asesorias" element={<p>lista de asesorías</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AsesorPendiente', () => {
  it('anuncia el título de la pantalla desde la que se llegó', () => {
    montar('Mi horario')
    expect(screen.getByRole('heading', { name: 'Mi horario' })).toBeInTheDocument()
  })

  it('explica que la SAE aún no confirma el nombramiento', () => {
    montar()
    expect(screen.getByText(/pendiente de que la SAE confirme tu nombramiento/i)).toBeInTheDocument()
  })

  it('ofrece volver a Asesorías', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Volver a Asesorías' }))
    expect(screen.getByText('lista de asesorías')).toBeInTheDocument()
  })
})
