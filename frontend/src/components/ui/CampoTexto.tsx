import { useId, type ChangeEvent } from 'react'

/** Mismo outline que ya expresan `Boton.tsx`, `Login.tsx` y `Landing.tsx` con
 *  utilidades de Tailwind (herencia de la Decisión 8 del plan de login
 *  frontend). Converger todo eso sobre la clase `.foco-visible` de `index.css`
 *  es un cambio aparte, con sus propios tests — aquí solo se centraliza el
 *  string para no repetirlo en cada pantalla. */
export const FOCO_VISIBLE =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary'

interface CampoTextoProps {
  etiqueta: string
  tipo: string
  valor: string
  autoComplete: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
}

export function CampoTexto({ etiqueta, tipo, valor, autoComplete, onChange }: CampoTextoProps) {
  const id = useId()
  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="absolute -top-2 left-3 z-10 bg-background px-1 text-xs text-on-surface-variant"
      >
        {etiqueta}
      </label>
      <input
        id={id}
        type={tipo}
        value={valor}
        onChange={onChange}
        autoComplete={autoComplete}
        required
        className={`h-14 w-full rounded-md border border-outline bg-transparent px-3.5 text-sm text-on-surface focus:border-primary ${FOCO_VISIBLE}`}
      />
    </div>
  )
}
