import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { solicitarResetDePassword } from '../auth/password'
import { Boton } from '../components/ui/Boton'
import { CampoTexto, FOCO_VISIBLE } from '../components/ui/CampoTexto'

export function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await solicitarResetDePassword(email)
      setEnviado(true)
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 429
          ? 'Demasiadas solicitudes. Espera una hora antes de volver a intentar.'
          : 'No se pudo enviar el correo. Intenta de nuevo.',
      )
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

      <h1 className="mb-2 text-lg font-semibold text-on-background">Recuperar contraseña</h1>
      <p className="mb-8 text-sm text-on-surface-variant">
        Te enviamos un enlace para crear una contraseña nueva. Si entras con tu Correo Ciencias, usa
        el botón de Google en la pantalla de acceso.
      </p>

      {enviado ? (
        <p role="status" className="entrada-lista text-sm text-on-surface-variant">
          Si ese correo pertenece a una cuenta con contraseña, ya va en camino un enlace para
          restablecerla. Revisa tu bandeja de entrada y la carpeta de spam.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <CampoTexto
            etiqueta="Correo"
            tipo="email"
            autoComplete="email"
            valor={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          {error && (
            <p role="alert" className="entrada-lista text-sm text-error">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando}>
            Enviar enlace
          </Boton>
        </form>
      )}
    </main>
  )
}
