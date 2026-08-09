import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { RutaDeAsesor } from './RutaProtegida'
import * as client from '../api/client'
import { usuarioDePrueba } from '../test/factories'

function montar() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/asesorias']}>
        <Routes>
          <Route
            path="/asesorias"
            element={
              <RutaDeAsesor>
                <p>panel del asesor</p>
              </RutaDeAsesor>
            }
          />
          <Route path="/home" element={<p>pantalla home</p>} />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaDeAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar al asesor académico', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ roles: ['academico', 'asesor_academico'] }),
    )

    montar()

    expect(await screen.findByText('panel del asesor')).toBeInTheDocument()
  })

  it('manda a Home a quien tiene sesión pero no es asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))

    montar()

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('panel del asesor')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))

    montar()

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })

  it('deja pasar al asesor aunque su perfil esté inactivo', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: false },
      }),
    )

    montar()

    expect(await screen.findByText('panel del asesor')).toBeInTheDocument()
  })
})
