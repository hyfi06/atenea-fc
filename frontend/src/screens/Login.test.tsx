import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Login } from './Login'
import * as auth from '../auth/AuthContext'
import { ApiError } from '../api/client'

interface Dobles {
  loginWithPassword?: (email: string, password: string) => Promise<void>
  loginWithGoogle?: () => Promise<void>
}

function montar({ loginWithPassword = vi.fn(), loginWithGoogle = vi.fn() }: Dobles = {}) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status: 'unauthenticated',
    loginWithPassword,
    loginWithGoogle,
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<p>pantalla home</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function llenarCredenciales() {
  fireEvent.change(screen.getByLabelText('Correo'), {
    target: { value: 'ana@ciencias.unam.mx' },
  })
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'ClaveSegura123!' } })
}

describe('Login', () => {
  afterEach(() => vi.restoreAllMocks())

  it('los campos tienen label asociado y foco visible', () => {
    montar()

    const correo = screen.getByLabelText('Correo')
    expect(correo).toBeInTheDocument()
    expect(correo).toHaveClass('focus-visible:outline-2')
    expect(screen.getByLabelText('Contraseña')).toHaveClass('focus-visible:outline-primary')
  })

  it('envía las credenciales y navega a Home', async () => {
    const loginWithPassword = vi.fn().mockResolvedValue(undefined)
    montar({ loginWithPassword })

    llenarCredenciales()
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(loginWithPassword).toHaveBeenCalledWith('ana@ciencias.unam.mx', 'ClaveSegura123!')
  })

  it('muestra el mensaje de credenciales inválidas cuando el backend responde 400', async () => {
    montar({
      loginWithPassword: vi.fn().mockRejectedValue(new ApiError(400, { non_field_errors: ['x'] })),
    })

    llenarCredenciales()
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('el botón de Google usa loginWithGoogle y navega solo si resuelve', async () => {
    const loginWithGoogle = vi.fn().mockResolvedValue(undefined)
    montar({ loginWithGoogle })

    fireEvent.click(screen.getByRole('button', { name: 'Continuar con Correo Ciencias' }))

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(loginWithGoogle).toHaveBeenCalledTimes(1)
  })

  it('si el login con Google falla, muestra el error y no navega', async () => {
    montar({ loginWithGoogle: vi.fn().mockRejectedValue(new Error('popup cerrado')) })

    fireEvent.click(screen.getByRole('button', { name: 'Continuar con Correo Ciencias' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo iniciar sesión con Google.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })
})
