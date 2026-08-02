import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import * as client from '../api/client'

function Sonda() {
  const { status, user } = useAuth()
  return <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
}

describe('AuthProvider', () => {
  afterEach(() => vi.restoreAllMocks())

  it('pasa a unauthenticated si /api/auth/user/ responde 401 al montar', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))

    render(
      <AuthProvider>
        <Sonda />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated:sin-usuario')
    })
  })

  it('pasa a authenticated con el usuario si /api/auth/user/ responde ok', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue({ pk: 1, email: 'asesor@ciencias.unam.mx', first_name: 'Ana' })

    render(
      <AuthProvider>
        <Sonda />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('authenticated:asesor@ciencias.unam.mx')
    })
  })
})
