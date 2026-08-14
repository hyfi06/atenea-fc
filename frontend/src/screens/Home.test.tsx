import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Home } from './Home'
import * as rol from '../auth/rol'
import * as auth from '../auth/AuthContext'
import { usuarioDePrueba } from '../test/factories'

function montar(esMiembroSAE: boolean) {
  vi.spyOn(rol, 'useEsMiembroSAE').mockReturnValue(esMiembroSAE)
  // Home monta MenuUsuario, que llama a useAuth: sin este doble el hook
  // lanza por falta de AuthProvider.
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: usuarioDePrueba(),
    roles: [],
    status: 'authenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Home', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra la tarjeta de la SAE al miembro de la SAE', () => {
    montar(true)
    expect(screen.getByRole('button', { name: 'Asesorías · SAE' })).toBeInTheDocument()
  })

  it('no muestra la tarjeta de la SAE a quien no tiene el rol', () => {
    montar(false)
    expect(screen.queryByRole('button', { name: 'Asesorías · SAE' })).not.toBeInTheDocument()
  })

  it('la tarjeta de la SAE navega al área SAE', () => {
    montar(true)
    fireEvent.click(screen.getByRole('button', { name: 'Asesorías · SAE' }))
    expect(screen.getByText('área SAE')).toBeInTheDocument()
  })

  it('sigue mostrando el resto de servicios', () => {
    montar(false)
    expect(screen.getByText('Becas')).toBeInTheDocument()
  })

  it('la hamburguesa del header abre el menú de la sesión', () => {
    montar(false)
    fireEvent.click(screen.getByRole('button', { name: 'Menú' }))
    expect(screen.getByText('usuaria@ciencias.unam.mx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })
})