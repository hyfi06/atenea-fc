import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { RutaDeAsesor, RutaDeAsesorias, RutaDeSAE, RutaConSesion } from './RutaProtegida'
import * as client from '../api/client'
import { usuarioDePrueba, usuarioSAE } from '../test/factories'

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

function montarAsesorias() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/asesorias']}>
        <Routes>
          <Route
            path="/asesorias"
            element={
              <RutaDeAsesorias>
                <p>vista de asesorías</p>
              </RutaDeAsesorias>
            }
          />
          <Route path="/home" element={<p>pantalla home</p>} />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaDeAsesorias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar al alumno', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    montarAsesorias()
    expect(await screen.findByText('vista de asesorías')).toBeInTheDocument()
  })

  it('deja pasar al asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ roles: ['academico', 'asesor_academico'] }),
    )
    montarAsesorias()
    expect(await screen.findByText('vista de asesorías')).toBeInTheDocument()
  })

  it('manda a Home a quien no es alumno ni asesor ni académico', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: [] }))
    montarAsesorias()
    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('vista de asesorías')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    montarAsesorias()
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })

  it('RutaDeAsesorias deja pasar al académico sin perfil de asesor', async () => {
    // Es la puerta al autoservicio de registro: sin esto, un académico que
    // toca el tile de Asesorías rebota a /home y no encuentra dónde darse de alta.
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['academico'] }))
    montarAsesorias()
    expect(await screen.findByText('vista de asesorías')).toBeInTheDocument()
  })
})

function montarSAE() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/sae/asesorias']}>
        <Routes>
          <Route
            path="/sae/asesorias"
            element={
              <RutaDeSAE>
                <p>área SAE</p>
              </RutaDeSAE>
            }
          />
          <Route path="/home" element={<p>pantalla home</p>} />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaDeSAE', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar al miembro de la SAE', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioSAE())
    montarSAE()
    expect(await screen.findByText('área SAE')).toBeInTheDocument()
  })

  it('manda a Home a quien tiene sesión pero no es SAE', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ roles: ['alumno', 'asesor_academico'] }),
    )
    montarSAE()
    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('área SAE')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    montarSAE()
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})

function montarConSesion() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route
            path="/home"
            element={
              <RutaConSesion>
                <p>pantalla home</p>
              </RutaConSesion>
            }
          />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaConSesion', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar a cualquier usuario con sesión', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    montarConSesion()
    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
  })

  it('deja pasar a un usuario con sesión aunque no tenga roles', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: [] }))
    montarConSesion()
    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('pantalla login')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    montarConSesion()
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('muestra el spinner mientras se resuelve la sesión', () => {
    vi.spyOn(client, 'apiGet').mockReturnValue(new Promise(() => {}))
    montarConSesion()
    expect(screen.getByLabelText('Cargando')).toBeInTheDocument()
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })
})
