/**
 * Google Identity Services — "Sign In With Google" (`google.accounts.id`).
 *
 * ADR 0019: se dejó `google.accounts.oauth2.initTokenClient` (que entrega un
 * access_token de OAuth) porque el backend, al validar ese token, no
 * comprobaba que se hubiera emitido para el client_id de Atenea. El ID token
 * es un JWT firmado por Google cuyo `audience` el backend sí verifica.
 */

export interface RespuestaCredencial {
  credential?: string
}

export interface NotificacionPrompt {
  isNotDisplayed?: () => boolean
  isSkippedMoment?: () => boolean
  isDismissedMoment?: () => boolean
  getDismissedReason?: () => string
}

interface ConfigInitialize {
  client_id: string
  callback: (respuesta: RespuestaCredencial) => void
  auto_select?: boolean
  cancel_on_tap_outside?: boolean
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize(config: ConfigInitialize): void
          prompt(listener?: (notificacion: NotificacionPrompt) => void): void
          cancel(): void
        }
      }
    }
  }
}

// Si One Tap no se muestra ni se cierra (caso posible con FedCM, donde las
// notificaciones dejan de ser informativas), la promesa nunca se resolvería y
// el botón quedaría girando para siempre. Ver Decisión 2 del plan.
const MS_ESPERA_ONE_TAP = 60_000

let cargando: Promise<void> | null = null

export function cargarGoogleIdentityServices(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve()
  if (cargando) return cargando

  cargando = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => {
      // Se limpia la promesa fallida para que un fallo de red transitorio no
      // deje el login roto por el resto de la sesión del navegador.
      cargando = null
      reject(new Error('No se pudo cargar Google Identity Services.'))
    }
    document.head.appendChild(script)
  })
  return cargando
}

function promptSinCredencial(notificacion: NotificacionPrompt): boolean {
  try {
    if (notificacion.isNotDisplayed?.()) return true
    if (notificacion.isSkippedMoment?.()) return true
    // El momento también se marca como "dismissed" en el camino feliz, con
    // motivo `credential_returned`: ahí no hay nada que rechazar.
    return (
      (notificacion.isDismissedMoment?.() ?? false) &&
      notificacion.getDismissedReason?.() !== 'credential_returned'
    )
  } catch {
    // En modo FedCM estos métodos pueden no estar disponibles y lanzar. Sin
    // señal utilizable no se rechaza: el callback de credencial sigue siendo
    // el único camino de éxito, y el timeout cubre el caso sin respuesta.
    return false
  }
}

export async function solicitarIdTokenDeGoogle(clientId: string): Promise<string> {
  await cargarGoogleIdentityServices()
  const id = window.google!.accounts.id

  return new Promise<string>((resolve, reject) => {
    let temporizador: ReturnType<typeof setTimeout>

    const terminar = (accion: () => void) => {
      clearTimeout(temporizador)
      accion()
    }

    temporizador = setTimeout(() => {
      id.cancel()
      reject(new Error('Login con Google cancelado.'))
    }, MS_ESPERA_ONE_TAP)

    id.initialize({
      client_id: clientId,
      // Sin `scope`: el ID token trae email/name/sub por defecto. Pedir un
      // scope OAuth sería pedir autorización para llamar APIs de Google a
      // nombre del usuario, que Atenea no hace (ADR 0019).
      callback: (respuesta) =>
        terminar(() =>
          respuesta.credential
            ? resolve(respuesta.credential)
            : reject(new Error('Login con Google cancelado.')),
        ),
      auto_select: false,
      cancel_on_tap_outside: true,
    })

    id.prompt((notificacion) => {
      if (promptSinCredencial(notificacion)) {
        terminar(() => reject(new Error('Login con Google cancelado.')))
      }
    })
  })
}
