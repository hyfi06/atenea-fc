import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import * as client from '../api/client'
import * as google from './google'
import { usuarioDePrueba } from '../test/factories'
import type { AuthUser } from '../api/types'

function Sonda() {
  const { status, user, roles, loginWithPassword, loginWithGoogle } = useAuth()
  return (
    <>
      <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
      <div data-testid="roles">{roles.join(',') || 'sin-roles'}</div>
      <button type="button" onClick={() => loginWithPassword('a@ciencias.unam.mx', 'x')}>
        Entrar con contraseña
      </button>
      <button type="button" onClick={() => loginWithGoogle()}>
        Entrar con Google
      </button>
    </>
  )
}

function montar() {
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )
}

describe('AuthProvider', () => {
  afterEach(() => vi.restoreAllMocks())

  it('pasa a unauthenticated si /api/auth/user/ responde 401 al montar', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated:sin-usuario')
    })
    expect(screen.getByTestId('roles')).toHaveTextContent('sin-roles')
  })

  it('pasa a authenticated con el usuario si /api/auth/user/ responde ok', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ email: 'asesor@ciencias.unam.mx' }),
    )

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('authenticated:asesor@ciencias.unam.mx')
    })
  })

  it('expone los roles que trae el usuario autenticado', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_academico: { id: 7, numero_trabajador: '12345' },
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: true },
      }),
    )

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('roles')).toHaveTextContent('academico,asesor_academico')
    })
  })

  it('no revienta si la respuesta todavía no trae roles (backend previo al plan del paso 4)', async () => {
    // El contrato de `roles` lo agrega la Task 3 del plan de backend, aún sin
    // ejecutar. Mientras tanto la app debe arrancar autenticada y sin roles,
    // no romperse al leer una propiedad ausente.
    const usuarioViejo = { pk: 1, email: 'vieja@ciencias.unam.mx', first_name: 'Ana' } as unknown as AuthUser
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioViejo)

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('authenticated:vieja@ciencias.unam.mx')
    })
    expect(screen.getByTestId('roles')).toHaveTextContent('sin-roles')
  })

  it('el rol llega con el login mismo, sin una segunda llamada a /api/auth/user/', async () => {
    const apiGet = vi
      .spyOn(client, 'apiGet')
      .mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    vi.spyOn(client, 'apiPost').mockResolvedValue({
      access: 'jwt-access',
      refresh: 'jwt-refresh',
      user: usuarioDePrueba({
        roles: ['alumno'],
        perfil_alumno: {
          id: 4,
          numero_cuenta: '312345678',
          carrera: 5,
          carrera_nombre: 'Actuaría',
          generacion: 2023,
        },
      }),
    })

    montar()
    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated'))

    fireEvent.click(screen.getByRole('button', { name: 'Entrar con contraseña' }))

    await waitFor(() => expect(screen.getByTestId('roles')).toHaveTextContent('alumno'))
    expect(apiGet).toHaveBeenCalledTimes(1)
  })

  it('manda a POST /api/auth/google/ el id_token que devuelve Google', async () => {
    vi.stubEnv('VITE_GOOGLE_OAUTH_CLIENT_ID', 'client-id-de-prueba')
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    const solicitar = vi.spyOn(google, 'solicitarIdTokenDeGoogle').mockResolvedValue('jwt-de-google')
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({
      access: 'jwt-access',
      refresh: 'jwt-refresh',
      user: usuarioDePrueba({ roles: ['alumno'] }),
    })

    montar()
    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated'))

    fireEvent.click(screen.getByRole('button', { name: 'Entrar con Google' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/auth/google/', { id_token: 'jwt-de-google' }),
    )
    expect(solicitar).toHaveBeenCalledWith('client-id-de-prueba')
    vi.unstubAllEnvs()
  })
})
