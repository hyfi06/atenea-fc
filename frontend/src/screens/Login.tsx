import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import { Boton } from '../components/ui/Boton'
import { CampoTexto, FOCO_VISIBLE } from '../components/ui/CampoTexto'
import { PantallaCargando } from '../components/PantallaCargando'

export function Login() {
  const navigate = useNavigate()
  const { loginWithPassword, loginWithGoogle, status } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Mismo guard que Landing: son dos entradas a la misma acción.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'authenticated') return <Navigate to="/home" replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await loginWithPassword(email, password)
      navigate('/home')
    } catch (err) {
      setError(
        err instanceof ApiError
          ? 'Correo o contraseña incorrectos.'
          : 'No se pudo iniciar sesión. Intenta de nuevo.',
      )
    } finally {
      setEnviando(false)
    }
  }

  async function handleGoogleLogin() {
    setError(null)
    setConectandoGoogle(true)
    try {
      await loginWithGoogle()
      navigate('/home')
    } catch {
      setError('No se pudo iniciar sesión con Google.')
    } finally {
      setConectandoGoogle(false)
    }
  }

  return (
    <main className="flex min-h-svh flex-col px-6 py-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        aria-label="Volver"
        className={`mb-8 flex h-9 w-9 items-center justify-center rounded-full text-on-background ${FOCO_VISIBLE}`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden>
          <path d="M15 19 L8 12 L15 5" />
        </svg>
      </button>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <CampoTexto etiqueta="Correo" tipo="email" autoComplete="email" valor={email} onChange={(e) => setEmail(e.target.value)} />
        <CampoTexto etiqueta="Contraseña" tipo="password" autoComplete="current-password" valor={password} onChange={(e) => setPassword(e.target.value)} />

        {error && (
          <p role="alert" className="entrada-lista text-sm text-error">
            {error}
          </p>
        )}

        <button type="button" className={`self-end rounded-md text-xs font-medium text-primary ${FOCO_VISIBLE}`}>
          ¿Olvidaste tu contraseña?
        </button>

        <Boton type="submit" cargando={enviando}>
          Entrar
        </Boton>

        <div className="flex items-center gap-3 text-xs text-on-surface-variant">
          <span className="h-px flex-1 bg-outline-variant" />
          o
          <span className="h-px flex-1 bg-outline-variant" />
        </div>

        <Boton type="button" variante="secundario" onClick={handleGoogleLogin} cargando={conectandoGoogle}>
          Continuar con Correo Ciencias
        </Boton>
      </form>
    </main>
  )
}
