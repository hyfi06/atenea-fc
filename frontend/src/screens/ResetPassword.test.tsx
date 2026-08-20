import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ResetPassword } from './ResetPassword'
import * as password from '../auth/password'
import { ApiError } from '../api/client'

function montar() {
  render(
    <MemoryRouter initialEntries={['/reset-password/MQ/abc-123/']}>
      <Routes>
        <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function llenar(nueva: string, confirmacion: string) {
  fireEvent.change(screen.getByLabelText('Contraseña nueva'), { target: { value: nueva } })
  fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { value: confirmacion } })
}

function enviar() {
  fireEvent.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))
}

describe('ResetPassword', () => {
  afterEach(() => vi.restoreAllMocks())

  it('los campos tienen label asociado y foco visible', () => {
    montar()

    expect(screen.getByLabelText('Contraseña nueva')).toHaveClass('focus-visible:outline-primary')
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
  })

  it('manda uid y token de la URL junto con las dos contraseñas', async () => {
    const confirmar = vi
      .spyOn(password, 'confirmarResetDePassword')
      .mockResolvedValue({ detail: 'ok' })
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()

    expect(await screen.findByRole('status')).toHaveTextContent('Tu contraseña quedó actualizada.')
    expect(confirmar).toHaveBeenCalledWith({
      uid: 'MQ',
      token: 'abc-123',
      password1: 'NuevaClave123!',
      password2: 'NuevaClave123!',
    })
  })

  it('si las contraseñas no coinciden avisa sin llamar al backend', async () => {
    const confirmar = vi.spyOn(password, 'confirmarResetDePassword')
    montar()

    llenar('NuevaClave123!', 'OtraClave123!')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent('Las contraseñas no coinciden.')
    expect(confirmar).not.toHaveBeenCalled()
  })

  it('con 400 en token muestra que el enlace ya no sirve', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockRejectedValue(
      new ApiError(400, { token: ['Invalid value'] }),
    )
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent('El enlace no es válido o ya expiró.')
  })

  it('con 400 de validación muestra el mensaje del backend', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockRejectedValue(
      new ApiError(400, { new_password2: ['Esta contraseña es demasiado corta.'] }),
    )
    montar()

    llenar('corta', 'corta')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Esta contraseña es demasiado corta.',
    )
  })

  it('con 429 muestra el mensaje de demasiados intentos', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockRejectedValue(
      new ApiError(429, { detail: 'Request was throttled.' }),
    )
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiados intentos.')
  })

  it('tras el éxito ofrece ir a iniciar sesión', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockResolvedValue({ detail: 'ok' })
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()
    fireEvent.click(await screen.findByRole('button', { name: 'Ir a iniciar sesión' }))

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
