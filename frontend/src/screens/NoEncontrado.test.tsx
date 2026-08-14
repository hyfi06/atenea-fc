import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { NoEncontrado } from './NoEncontrado'

function montar(ruta: string) {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <Routes>
        <Route path="/" element={<p>pantalla landing</p>} />
        <Route path="*" element={<NoEncontrado />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('NoEncontrado', () => {
  it('la ruta comodín atrapa cualquier dirección desconocida', () => {
    montar('/ruta-que-no-existe')

    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
  })

  it('no se interpone con las rutas que sí existen', () => {
    montar('/')

    expect(screen.getByText('pantalla landing')).toBeInTheDocument()
    expect(screen.queryByText('404')).not.toBeInTheDocument()
  })

  it('el botón de salida lleva a la raíz', () => {
    montar('/otra-direccion-inventada')

    fireEvent.click(screen.getByRole('button', { name: 'Volver al inicio' }))

    expect(screen.getByText('pantalla landing')).toBeInTheDocument()
  })
})
