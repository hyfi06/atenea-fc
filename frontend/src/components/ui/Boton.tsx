import type { ButtonHTMLAttributes } from 'react'

interface BotonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  cargando?: boolean
  variante?: 'primario' | 'secundario' | 'peligro'
}

const VARIANTES: Record<NonNullable<BotonProps['variante']>, string> = {
  primario: 'bg-primary text-on-primary',
  secundario: 'border border-outline text-primary',
  peligro: 'bg-error-container text-on-error-container',
}

export function Boton({ cargando = false, variante = 'primario', disabled, children, className = '', ...props }: BotonProps) {
  return (
    <button
      disabled={disabled || cargando}
      className={`presionable flex h-11 items-center justify-center gap-2 rounded-full text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60 ${VARIANTES[variante]} ${className}`}
      {...props}
    >
      {cargando && <span className="spinner h-4 w-4" aria-hidden />}
      {children}
    </button>
  )
}
