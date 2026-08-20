import { describe, it, expect, vi, afterEach } from 'vitest'
import * as client from '../api/client'
import { solicitarResetDePassword, confirmarResetDePassword } from './password'

describe('auth/password', () => {
  afterEach(() => vi.restoreAllMocks())

  it('solicitar manda el correo al endpoint de reset', async () => {
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({ detail: 'ok' })

    await solicitarResetDePassword('ana@ciencias.unam.mx')

    expect(apiPost).toHaveBeenCalledWith('/api/auth/password/reset/', {
      email: 'ana@ciencias.unam.mx',
    })
  })

  it('confirmar traduce los nombres de campo que espera dj-rest-auth', async () => {
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({ detail: 'ok' })

    await confirmarResetDePassword({
      uid: 'MQ',
      token: 'abc-123',
      password1: 'NuevaClave123!',
      password2: 'NuevaClave123!',
    })

    expect(apiPost).toHaveBeenCalledWith('/api/auth/password/reset/confirm/', {
      uid: 'MQ',
      token: 'abc-123',
      new_password1: 'NuevaClave123!',
      new_password2: 'NuevaClave123!',
    })
  })
})
