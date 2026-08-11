import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { useEsAsesor, useEsAlumno, useEsMiembroSAE } from './rol'

function PantallaCargando() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="spinner h-6 w-6 text-primary" aria-label="Cargando" />
    </div>
  )
}

export function RutaDeAsesor({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAsesor = useEsAsesor()
  const location = useLocation()

  // Antes había dos estados de carga (el de la sesión y el del sondeo de rol).
  // Ahora el rol llega con la sesión, así que `status` es la única compuerta.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esAsesor) return <Navigate to="/home" replace />

  return <>{children}</>
}

export function RutaDeAsesorias({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esAsesor && !esAlumno) return <Navigate to="/home" replace />

  return <>{children}</>
}


export function RutaDeSAE({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esMiembroSAE = useEsMiembroSAE()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esMiembroSAE) return <Navigate to="/home" replace />

  return <>{children}</>
}