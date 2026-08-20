import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { confirmarResetDePassword } from '../auth/password'
import { Boton } from '../components/ui/Boton'
import { CampoTexto, FOCO_VISIBLE } from '../components/ui/CampoTexto'

const ERROR_GENERICO = 'No se pudo cambiar la contraseña. Intenta de nuevo.'

/** El backend responde 400 con `{campo: [mensaje]}` (validación de DRF). Los
 *  mensajes de contraseña ya vienen traducidos (LANGUAGE_CODE = "es-mx"), así
 *  que se muestran tal cual; `uid`/`token` sí se traducen a algo accionable. */
function mensajeDeError(err: unknown): string {
  if (!(err instanceof ApiError)) return ERROR_GENERICO
  if (err.status === 429) return 'Demasiados intentos. Espera una hora antes de volver a intentar.'
  const body = err.body as Record<string, string[] | undefined> | null
  if (body?.uid || body?.token) return 'El enlace no es válido o ya expiró. Solicita uno nuevo.'
  return body?.new_password2?.[0] ?? body?.new_password1?.[0] ?? ERROR_GENERICO
}

export function ResetPassword() {
  const navigate = useNavigate()
  const { uid = '', token = '' } = useParams<{ uid: string; token: string }>()
  const [password1, setPassword1] = useState('')
  const [password2, setPassword2] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [listo, setListo] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    // Se valida antes de llamar: el confirm tiene un cupo de 10/hour y no vale
    // la pena gastarlo en un error que el cliente puede ver por su cuenta.
    if (password1 !== password2) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setEnviando(true)
    try {
      await confirmarResetDePassword({ uid, token, password1, password2 })
      setListo(true)
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex min-h-svh flex-col px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/login')}
        aria-label="Volver"
        className={`mb-8 flex h-9 w-9 items-center justify-center rounded-full text-on-background ${FOCO_VISIBLE}`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden>
          <path d="M15 19 L8 12 L15 5" />
        </svg>
      </button>

      <h1 className="mb-2 text-lg font-semibold text-on-background">Nueva contraseña</h1>
      <p className="mb-8 text-sm text-on-surface-variant">
        Escríbela dos veces para confirmar que quedó como querías.
      </p>

      {listo ? (
        <div className="flex flex-col gap-6">
          <p role="status" className="entrada-lista text-sm text-on-surface-variant">
            Tu contraseña quedó actualizada.
          </p>
          <Boton type="button" onClick={() => navigate('/login')}>
            Ir a iniciar sesión
          </Boton>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <CampoTexto
            etiqueta="Contraseña nueva"
            tipo="password"
            autoComplete="new-password"
            valor={password1}
            onChange={(e) => setPassword1(e.target.value)}
          />
          <CampoTexto
            etiqueta="Confirmar contraseña"
            tipo="password"
            autoComplete="new-password"
            valor={password2}
            onChange={(e) => setPassword2(e.target.value)}
          />

          {error && (
            <p role="alert" className="entrada-lista text-sm text-error">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando}>
            Cambiar contraseña
          </Boton>
        </form>
      )}
    </main>
  )
}
