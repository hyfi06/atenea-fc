import type { ReactNode, SVGProps } from 'react'

export interface IconProps {
  className?: string
}

/**
 * Íconos de interfaz (no de servicio). `ServiceIcons.tsx` usa `viewBox` 48 y
 * trazo 2.5 porque son ilustraciones de tarjeta; estos son íconos de control
 * a 24px con trazo 2, la métrica que fija la spec del paso 3.
 *
 * Se dibujan a mano, sin librería de íconos (ADR 0014).
 */
function IconBase({ children, ...props }: SVGProps<SVGSVGElement> & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...props}
    >
      {children}
    </svg>
  )
}

/** Monitor — formato virtual. Mismo SVG en "Mi horario" y en el detalle. */
export function IconVirtual({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M8 20h8" />
      <path d="M12 16v4" />
    </IconBase>
  )
}

/** Pin — formato presencial. Mismo SVG en "Mi horario" y en el detalle. */
export function IconPresencial({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <circle cx="12" cy="10" r="3" />
      <path d="M12 21c-4-4.5-7-8-7-11a7 7 0 0 1 14 0c0 3-3 6.5-7 11Z" />
    </IconBase>
  )
}

/** Basura — quitar un elemento de una lista. */
export function IconBasura({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <path d="M4 7h16" />
      <path d="M10 4h4" />
      <path d="M6 7l1 13h10l1-13" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </IconBase>
  )
}
