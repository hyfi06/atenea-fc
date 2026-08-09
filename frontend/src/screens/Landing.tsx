import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Boton } from '../components/ui/Boton'
import { useAuth } from '../auth/AuthContext'

export function Landing() {
  const navigate = useNavigate()
  const { loginWithGoogle } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Mismo flujo, mismo manejo de carga/error y mismo copy de error que
  // Login.tsx: son dos entradas a la misma acción, no dos comportamientos.
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
    <main className="flex min-h-svh flex-col items-center justify-between px-6 py-12">
      <div />

      <div className="flex flex-col items-center gap-4 text-center">
        <Logo className="h-20 w-20 text-primary" />
        <h1 className="text-2xl font-semibold">Atenea</h1>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Secretaría de Asuntos Estudiantiles
        </p>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Facultad de Ciencias, UNAM
        </p>
      </div>

      <div className="flex w-full max-w-xs flex-col gap-3">
        {error && (
          <p role="alert" className="text-center text-sm text-error">
            {error}
          </p>
        )}

        <Boton type="button" onClick={handleGoogleLogin} cargando={conectandoGoogle}>
          Continuar con Correo Ciencias
        </Boton>

        <button
          type="button"
          onClick={() => navigate('/login')}
          className="h-11 rounded-full text-sm font-semibold text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          Entrar con correo y contraseña
        </button>
      </div>
    </main>
  )
}
