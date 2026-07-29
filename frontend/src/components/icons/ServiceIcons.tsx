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

export function IconOrientacionVocacional({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <circle cx="24" cy="24" r="18" />
      <path d="M31 17 L21 21 L17 31 L27 27 Z" />
      <circle cx="24" cy="24" r="1.6" fill="currentColor" stroke="none" />
    </IconBase>
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

export function IconBecas({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <path d="M24 12 L44 20 L24 28 L4 20 Z" />
      <path d="M14 24 L14 32 C14 35 19 38 24 38 C29 38 34 35 34 32 L34 24" />
      <path d="M40 20 L40 30" />
      <circle cx="40" cy="33" r="2" fill="currentColor" stroke="none" />
    </IconBase>
  )
}

export function IconIdiomas({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <rect x="4" y="8" width="26" height="16" rx="6" />
      <path d="M10 24 L7 31 L16 24 Z" />
      <line x1="9" y1="13" x2="25" y2="13" />
      <line x1="9" y1="18" x2="20" y2="18" />
      <rect x="18" y="22" width="26" height="16" rx="6" />
      <path d="M32 38 L35 45 L38 38 Z" />
      <line x1="23" y1="27" x2="39" y2="27" />
      <line x1="23" y1="32" x2="34" y2="32" />
    </IconBase>
  )
}

const HANDSHAKE_PATH =
  'M475-160q4 0 8-2t6-4l328-328q12-12 17.5-27t5.5-30q0-16-5.5-30.5T817-607L647-777q-11-12-25.5-17.5T591-800q-15 0-30 5.5T534-777l-11 11 74 75q15 14 22 32t7 38q0 42-28.5 70.5T527-522q-20 0-38.5-7T456-550l-75-74-175 175q-3 3-4.5 6.5T200-435q0 8 6 14.5t14 6.5q4 0 8-2t6-4l136-136 56 56-135 136q-3 3-4.5 6.5T285-350q0 8 6 14t14 6q4 0 8-2t6-4l136-135 56 56-135 136q-3 2-4.5 6t-1.5 8q0 8 6 14t14 6q4 0 7.5-1.5t6.5-4.5l136-135 56 56-136 136q-3 3-4.5 6.5T454-180q0 8 6.5 14t14.5 6Zm-1 80q-37 0-65.5-24.5T375-166q-34-5-57-28t-28-57q-34-5-56.5-28.5T206-336q-38-5-62-33t-24-66q0-20 7.5-38.5T149-506l232-231 131 131q2 3 6 4.5t8 1.5q9 0 15-5.5t6-14.5q0-4-1.5-8t-4.5-6L398-777q-11-12-25.5-17.5T342-800q-15 0-30 5.5T285-777L144-635q-9 9-15 21t-8 24q-2 12 0 24.5t8 23.5l-58 58q-17-23-25-50.5T40-590q2-28 14-54.5T87-692l141-141q24-23 53.5-35t60.5-12q31 0 60.5 12t52.5 35l11 11 11-11q24-23 53.5-35t60.5-12q31 0 60.5 12t52.5 35l169 169q23 23 35 53t12 61q0 31-12 60.5T873-437L545-110q-14 14-32.5 22T474-80Zm-99-560Z'

/**
 * A diferencia de los demás íconos de este archivo (trazo), este usa el ícono
 * "handshake" de Google Material Symbols (Apache License 2.0), relleno.
 * https://fonts.google.com/icons
 */
export function IconServicioSocial({ className }: IconProps) {
  return (
    <svg viewBox="0 -960 960 960" fill="currentColor" className={className} role="img" aria-label="Servicio Social">
      <path d={HANDSHAKE_PATH} />
    </svg>
  )
}

export function IconBolsaDeTrabajo({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <rect x="8" y="18" width="32" height="22" rx="4" />
      <path d="M18 18 V13 C18 11 19 10 21 10 H27 C29 10 30 11 30 13 V18" />
      <line x1="8" y1="27" x2="40" y2="27" />
      <rect x="21" y="25" width="6" height="5" rx="1" />
    </IconBase>
  )
}

export function IconMovilidad({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <path d="M6 24 L42 8 L30 42 L23 27 L6 24 Z" />
      <path d="M23 27 L34 15" />
    </IconBase>
  )
}

export function IconVoluntariado({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <path d="M24 34 C14 26 10 20 10 15 C10 10 14 7 18 8 C21 9 23 11 24 14 C25 11 27 9 30 8 C34 7 38 10 38 15 C38 20 34 26 24 34 Z" />
      <path d="M8 34 C8 40 16 44 24 44 C32 44 40 40 40 34" />
    </IconBase>
  )
}

export function IconPracticasProfesionales({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <rect x="12" y="14" width="24" height="30" rx="5" />
      <path d="M20 14 V10 C20 8 21 7 23 7 H25 C27 7 28 8 28 10 V14" />
      <circle cx="24" cy="26" r="5" />
      <path d="M17 39 C17 34 20 32 24 32 C28 32 31 34 31 39" />
    </IconBase>
  )
}
