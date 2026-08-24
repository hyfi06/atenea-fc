import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { useEsAsesor, useEsAlumno, useEsMiembroSAE, useEsAcademico } from './rol'
import { PantallaCargando } from '../components/PantallaCargando'

export function RutaConSesion({ children }: { children: ReactNode }) {
  const { status } = useAuth()

  // Solo exige sesión, sin rol. `/home` es la página de aterrizaje de cualquier
  // usuario autenticado (los guards por rol redirigen aquí al fallar el rol), así
  // que no puede usar esos guards sin provocar un loop de redirección.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export function RutaDeAsesor({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAsesor = useEsAsesor()

  // Antes había dos estados de carga (el de la sesión y el del sondeo de rol).
  // Ahora el rol llega con la sesión, así que `status` es la única compuerta.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/" replace />
  }
  if (!esAsesor) return <Navigate to="/home" replace />

  return <>{children}</>
}

export function RutaDeAsesorias({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  const esAcademico = useEsAcademico()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/" replace />
  }
  if (!esAsesor && !esAlumno && !esAcademico) return <Navigate to="/home" replace />

  return <>{children}</>
}


export function RutaDeSAE({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esMiembroSAE = useEsMiembroSAE()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/" replace />
  }
  if (!esMiembroSAE) return <Navigate to="/home" replace />

  return <>{children}</>
}

export function RutaDeAcademico({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAcademico = useEsAcademico()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/" replace />
  }
  if (!esAcademico) return <Navigate to="/home" replace />

  return <>{children}</>
}
