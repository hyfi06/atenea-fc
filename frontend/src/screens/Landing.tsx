import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'

export function Landing() {
  const navigate = useNavigate()

  return (
    <main className="flex min-h-svh flex-col items-center justify-between px-6 py-12">
      <div />

      <div className="flex flex-col items-center gap-4 text-center">
        <Logo className="h-20 w-20 text-primary" />
        <h1 className="text-2xl font-semibold">Atenea</h1>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Servicios de la SAE — Facultad de Ciencias, UNAM
        </p>
      </div>

      <div className="flex w-full max-w-xs flex-col gap-3">
        <button
          type="button"
          className="h-11 rounded-full bg-primary text-sm font-semibold text-on-primary"
        >
          Continuar con Correo Ciencias
        </button>
        <button
          type="button"
          onClick={() => navigate('/login')}
          className="h-11 text-sm font-semibold text-primary"
        >
          Entrar con correo y contraseña
        </button>
      </div>
    </main>
  )
}
