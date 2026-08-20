import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ForgotPassword } from './ForgotPassword'
import * as password from '../auth/password'
import { ApiError } from '../api/client'

function montar() {
  render(
    <MemoryRouter initialEntries={['/forgot-password']}>
      <Routes>
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function llenarCorreo() {
  fireEvent.change(screen.getByLabelText('Correo'), {
    target: { value: 'ana@ciencias.unam.mx' },
  })
}

describe('ForgotPassword', () => {
  afterEach(() => vi.restoreAllMocks())

  it('el campo tiene label asociado y foco visible', () => {
    montar()

    const correo = screen.getByLabelText('Correo')
    expect(correo).toBeInTheDocument()
    expect(correo).toHaveClass('focus-visible:outline-primary')
  })

  it('manda el correo y muestra la confirmación sin revelar si la cuenta existe', async () => {
    const solicitar = vi
      .spyOn(password, 'solicitarResetDePassword')
      .mockResolvedValue({ detail: 'ok' })
    montar()

    llenarCorreo()
    fireEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    const confirmacion = await screen.findByRole('status')
    expect(confirmacion).toHaveTextContent('Si ese correo pertenece a una cuenta con contraseña')
    expect(solicitar).toHaveBeenCalledWith('ana@ciencias.unam.mx')
    expect(screen.queryByLabelText('Correo')).not.toBeInTheDocument()
  })

  it('con 429 muestra el mensaje de demasiadas solicitudes y deja el formulario', async () => {
    vi.spyOn(password, 'solicitarResetDePassword').mockRejectedValue(
      new ApiError(429, { detail: 'Request was throttled.' }),
    )
    montar()

    llenarCorreo()
    fireEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiadas solicitudes.')
    expect(screen.getByLabelText('Correo')).toBeInTheDocument()
  })

  it('con cualquier otro fallo muestra el error genérico', async () => {
    vi.spyOn(password, 'solicitarResetDePassword').mockRejectedValue(new Error('sin red'))
    montar()

    llenarCorreo()
    fireEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo enviar el correo.')
  })

  it('el botón de volver regresa al login', async () => {
    montar()

    fireEvent.click(screen.getByRole('button', { name: 'Volver' }))

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
