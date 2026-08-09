import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cargarGoogleIdentityServices, solicitarIdTokenDeGoogle, type NotificacionPrompt } from './google'

type RespuestaCredencial = { credential?: string }

/**
 * Sustituye la librería de Google por un doble que captura el callback de
 * credential y el listener de notificaciones, para poder dispararlos a mano.
 */
function montarGoogleFalso() {
  let callback: ((r: RespuestaCredencial) => void) | undefined
  let notificar: ((n: NotificacionPrompt) => void) | undefined

  const initialize = vi.fn((config: { client_id: string; callback: (r: RespuestaCredencial) => void }) => {
    callback = config.callback
  })
  const prompt = vi.fn((listener?: (n: NotificacionPrompt) => void) => {
    notificar = listener
  })
  const cancel = vi.fn()

  window.google = { accounts: { id: { initialize, prompt, cancel } } }

  return {
    initialize,
    prompt,
    cancel,
    responderCon: (r: RespuestaCredencial) => callback!(r),
    notificarCon: (n: NotificacionPrompt) => notificar!(n),
  }
}

describe('solicitarIdTokenDeGoogle', () => {
  afterEach(() => {
    delete window.google
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('inicializa Sign In With Google con el client_id y sin pedir ningún scope', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.initialize).toHaveBeenCalled())

    const config = google.initialize.mock.calls[0][0] as Record<string, unknown>
    expect(config.client_id).toBe('client-id-de-prueba')
    // ADR 0019: el id_token trae email/name/sub por sí solo. Pedir un scope
    // sería volver a pedir autorización de API, que es justo lo que se dejó.
    expect(config).not.toHaveProperty('scope')
    expect(google.prompt).toHaveBeenCalled()

    google.responderCon({ credential: 'jwt-de-google' })
    await expect(promesa).resolves.toBe('jwt-de-google')
  })

  it('resuelve con la credencial que entrega el callback', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.prompt).toHaveBeenCalled())
    google.responderCon({ credential: 'jwt-de-google' })

    await expect(promesa).resolves.toBe('jwt-de-google')
  })

  it('rechaza si One Tap no llegó a mostrarse', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.prompt).toHaveBeenCalled())
    google.notificarCon({ isNotDisplayed: () => true })

    await expect(promesa).rejects.toThrow('Login con Google cancelado.')
  })

  it('no rechaza cuando el momento se cierra porque ya devolvió la credencial', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.prompt).toHaveBeenCalled())
    // Camino feliz: Google marca el momento como "dismissed" con este motivo
    // justo cuando entrega la credencial. Mirar solo isDismissedMoment()
    // rechazaría un login exitoso.
    google.notificarCon({
      isDismissedMoment: () => true,
      getDismissedReason: () => 'credential_returned',
    })
    google.responderCon({ credential: 'jwt-de-google' })

    await expect(promesa).resolves.toBe('jwt-de-google')
  })

  it('rechaza y cancela One Tap si nadie responde en 60 s', async () => {
    vi.useFakeTimers()
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    const assertion = expect(promesa).rejects.toThrow('Login con Google cancelado.')
    await vi.advanceTimersByTimeAsync(60_000)

    await assertion
    expect(google.cancel).toHaveBeenCalled()
  })
})

describe('cargarGoogleIdentityServices', () => {
  beforeEach(() => {
    delete window.google
    document.head.innerHTML = ''
    vi.resetModules()
  })

  afterEach(() => {
    delete window.google
    document.head.innerHTML = ''
  })

  function scriptsDeGoogle() {
    return document.head.querySelectorAll('script[src="https://accounts.google.com/gsi/client"]')
  }

  it('inyecta el script de Google Identity Services si la librería no está en la página', async () => {
    const { cargarGoogleIdentityServices: cargar } = await import('./google')

    const promesa = cargar()
    const script = scriptsDeGoogle()[0] as HTMLScriptElement
    expect(script).toBeTruthy()
    expect(script.async).toBe(true)
    script.onload!(new Event('load'))

    await expect(promesa).resolves.toBeUndefined()
  })

  it('permite reintentar si el script falla al cargar', async () => {
    const { cargarGoogleIdentityServices: cargar } = await import('./google')

    const primera = cargar()
    ;(scriptsDeGoogle()[0] as HTMLScriptElement).onerror!(new Event('error'))
    await expect(primera).rejects.toThrow('No se pudo cargar Google Identity Services.')

    cargar()
    expect(scriptsDeGoogle()).toHaveLength(2)
  })
})

// Referencia usada solo para que el import de tipo no quede sin uso si se
// reordenan los tests; `cargarGoogleIdentityServices` se ejercita arriba.
void cargarGoogleIdentityServices
