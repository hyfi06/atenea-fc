import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { useEsAsesor } from './rol'

function PantallaCargando() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="spinner h-6 w-6 text-primary" aria-label="Cargando" />
    </div>
  )
}

export function RutaDeAsesor({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const { data: esAsesor, isPending } = useEsAsesor()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (isPending) return <PantallaCargando />
  if (!esAsesor) return <Navigate to="/home" replace />

  return <>{children}</>
}
