import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Home } from './Home'
import * as rol from '../auth/rol'
import * as auth from '../auth/AuthContext'
import { usuarioDePrueba } from '../test/factories'

interface Roles {
  alumno?: boolean
  academico?: boolean
  sae?: boolean
}

function montar({ alumno = false, academico = false, sae = false }: Roles = {}) {
  vi.spyOn(rol, 'useEsAlumno').mockReturnValue(alumno)
  vi.spyOn(rol, 'useEsAcademico').mockReturnValue(academico)
  vi.spyOn(rol, 'useEsMiembroSAE').mockReturnValue(sae)
  // Home monta MenuUsuario, que llama a useAuth: sin este doble el hook
  // lanza por falta de AuthProvider.
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: usuarioDePrueba(),
    roles: [],
    status: 'authenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
    refrescarSesion: vi.fn().mockResolvedValue(undefined),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/asesorias" element={<p>pantalla de asesorías</p>} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Home', () => {
  afterEach(() => vi.restoreAllMocks())

  it('no pinta ningún servicio mock', () => {
    montar({ alumno: true })
    expect(screen.queryByText('Becas')).not.toBeInTheDocument()
    expect(screen.queryByText('Movilidad')).not.toBeInTheDocument()
  })

  it('ofrece Asesorías al alumno', () => {
    montar({ alumno: true })
    fireEvent.click(screen.getByRole('button', { name: 'Asesorías' }))
    expect(screen.getByText('pantalla de asesorías')).toBeInTheDocument()
  })

  it('ofrece Asesorías al académico', () => {
    montar({ academico: true })
    expect(screen.getByRole('button', { name: 'Asesorías' })).toBeInTheDocument()
  })

  it('ofrece el panel SAE al miembro de la SAE', () => {
    montar({ sae: true })
    fireEvent.click(screen.getByRole('button', { name: 'Asesorías · SAE' }))
    expect(screen.getByText('área SAE')).toBeInTheDocument()
  })

  it('el alumno no ve el panel SAE', () => {
    montar({ alumno: true })
    expect(screen.queryByRole('button', { name: 'Asesorías · SAE' })).not.toBeInTheDocument()
  })

  it('sin roles, solo se ve la Guía de uso', () => {
    montar()
    expect(screen.getByRole('link', { name: 'Guía de uso' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Asesorías' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Asesorías · SAE' })).not.toBeInTheDocument()
  })

  it('la Guía de uso es un link a /docs/, visible para cualquier rol', () => {
    montar({ alumno: true })
    const link = screen.getByRole('link', { name: 'Guía de uso' })
    expect(link).toHaveAttribute('href', '/docs/')
  })

  it('la hamburguesa del header abre el menú de la sesión', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Menú' }))
    expect(screen.getByText('usuaria@ciencias.unam.mx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })
})