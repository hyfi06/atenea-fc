import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Landing } from './Landing'
import * as auth from '../auth/AuthContext'

function montar(loginWithGoogle: () => Promise<void>) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status: 'unauthenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle,
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/home" element={<p>pantalla home</p>} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function botonDeGoogle() {
  return screen.getByRole('button', { name: 'Continuar con Correo Ciencias' })
}

describe('Landing', () => {
  afterEach(() => vi.restoreAllMocks())

  it('navega a Home solo después de que el login resuelve', async () => {
    const loginWithGoogle = vi.fn().mockResolvedValue(undefined)
    montar(loginWithGoogle)

    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
    fireEvent.click(botonDeGoogle())

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(loginWithGoogle).toHaveBeenCalledTimes(1)
  })

  it('si el login falla, muestra el error y no navega', async () => {
    montar(vi.fn().mockRejectedValue(new Error('popup cerrado')))

    fireEvent.click(botonDeGoogle())

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo iniciar sesión con Google.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('deshabilita el botón mientras el login está en curso', async () => {
    // Promesa que nunca se resuelve: fija el estado "conectando".
    montar(vi.fn().mockReturnValue(new Promise<void>(() => {})))

    fireEvent.click(botonDeGoogle())

    expect(await screen.findByRole('button', { name: 'Continuar con Correo Ciencias' })).toBeDisabled()
  })

  it('el botón secundario sigue llevando al login con correo y contraseña', async () => {
    montar(vi.fn().mockResolvedValue(undefined))

    fireEvent.click(screen.getByRole('button', { name: 'Entrar con correo y contraseña' }))

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
