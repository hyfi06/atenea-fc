import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { MenuUsuario } from './MenuUsuario'
import * as auth from '../auth/AuthContext'
import { usuarioDePrueba } from '../test/factories'

type Estado = 'loading' | 'authenticated' | 'unauthenticated'

interface Opciones {
  status?: Estado
  logout?: () => Promise<void>
}

function montar({ status = 'authenticated', logout = vi.fn().mockResolvedValue(undefined) }: Opciones = {}) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: status === 'authenticated' ? usuarioDePrueba() : null,
    roles: [],
    status,
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout,
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<MenuUsuario />} />
        <Route path="/" element={<p>pantalla landing</p>} />
      </Routes>
    </MemoryRouter>,
  )
  return logout
}

function disparador() {
  return screen.getByRole('button', { name: 'Menú' })
}

function abrir() {
  fireEvent.click(disparador())
}

describe('MenuUsuario', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  /** El panel se desmunta cuando termina `.salida-menu` (140 ms). */
  function terminarSalida() {
    act(() => {
      vi.advanceTimersByTime(140)
    })
  }

  it('arranca cerrado', () => {
    montar()
    expect(disparador()).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('al abrirlo muestra la identidad de la sesión y la opción de cerrarla', () => {
    montar()
    abrir()
    expect(disparador()).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Ana López Ruiz')).toBeInTheDocument()
    expect(screen.getByText('usuaria@ciencias.unam.mx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })

  it('Escape lo cierra y devuelve el foco al disparador', () => {
    vi.useFakeTimers()
    montar()
    abrir()
    fireEvent.keyDown(document, { key: 'Escape' })

    // El foco vuelve de inmediato; el panel espera a que corra su salida.
    expect(disparador()).toHaveFocus()
    terminarSalida()

    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('el panel sigue montado mientras corre la animación de salida', () => {
    vi.useFakeTimers()
    montar()
    abrir()
    fireEvent.keyDown(document, { key: 'Escape' })

    const panel = screen.getByRole('button', { name: 'Cerrar sesión' }).parentElement
    expect(panel).toHaveClass('salida-menu')
    expect(panel).not.toHaveClass('entrada-menu')

    terminarSalida()

    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('un click fuera lo cierra', () => {
    vi.useFakeTimers()
    montar()
    abrir()
    fireEvent.mouseDown(document.body)
    terminarSalida()

    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('cerrar sesión llama a logout una vez y lleva a la landing', async () => {
    const logout = montar()
    abrir()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByText('pantalla landing')).toBeInTheDocument()
    expect(logout).toHaveBeenCalledTimes(1)
  })

  it('sin sesión no dibuja el disparador', () => {
    montar({ status: 'unauthenticated' })
    expect(screen.queryByRole('button', { name: 'Menú' })).not.toBeInTheDocument()
  })
})
