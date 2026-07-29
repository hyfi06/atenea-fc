interface LogoProps {
  className?: string
}

export function Logo({ className }: LogoProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      stroke="currentColor"
      strokeWidth={3.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      role="img"
      aria-label="Atenea"
    >
      <circle cx="32" cy="32" r="27" />
      <path d="M20 32 C20 19 25 14 32 14 C39 14 44 19 44 32" />
      <path d="M20 32 L18 43 L24 46 L26 35" />
      <path d="M44 32 L46 43 L40 46 L38 35" />
      <path d="M32 22 L32 44" />
      <path d="M22 14 Q32 3 42 14" />
    </svg>
  )
}
