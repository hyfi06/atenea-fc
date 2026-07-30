import { useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

interface TextFieldProps {
  label: string
  type: string
  value: string
  autoComplete: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
}

function TextField({ label, type, value, autoComplete, onChange }: TextFieldProps) {
  return (
    <label className="relative block">
      <span className="absolute -top-2 left-3 bg-background px-1 text-xs text-on-surface-variant">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        required
        className="h-14 w-full rounded-md border border-outline bg-transparent px-3.5 text-sm text-on-surface outline-none focus:border-primary"
      />
    </label>
  )
}

export function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    navigate('/home')
  }

  return (
    <main className="flex min-h-svh flex-col px-6 py-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        aria-label="Volver"
        className="mb-8 flex h-9 w-9 items-center justify-center text-on-background"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
          <path d="M15 19 L8 12 L15 5" />
        </svg>
      </button>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <TextField label="Correo" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField label="Contraseña" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />

        <button type="button" className="self-end text-xs font-medium text-primary">
          ¿Olvidaste tu contraseña?
        </button>

        <button type="submit" className="h-11 rounded-full bg-primary text-sm font-semibold text-on-primary">
          Entrar
        </button>

        <div className="flex items-center gap-3 text-xs text-on-surface-variant">
          <span className="h-px flex-1 bg-outline-variant" />
          o
          <span className="h-px flex-1 bg-outline-variant" />
        </div>

        <button
          type="button"
          onClick={() => navigate('/home')}
          className="h-11 rounded-full border border-outline text-sm font-semibold text-primary"
        >
          Continuar con Correo Ciencias
        </button>
      </form>
    </main>
  )
}
