/**
 * Íconos de servicios de la SAE. Hoy solo sobrevive el de Asesorías: los ocho
 * de los servicios mock se borraron junto con `data/services.ts` al retirarlos
 * de Home (ADR 0027 decisión 9). Vuelven cuando exista el servicio de verdad.
 */

import type { ReactNode, SVGProps } from 'react'

export interface IconProps {
  className?: string
}

function IconBase({ children, ...props }: SVGProps<SVGSVGElement> & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  )
}

export function IconTutorias({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <circle cx="18" cy="16" r="6" />
      <path d="M8 34 C8 26 12 22 18 22 C24 22 28 26 28 34" />
      <circle cx="33" cy="21" r="5" />
      <path d="M25 36 C25 30 29 27 33 27 C38 27 41 30 41 36" />
    </IconBase>
  )
}
