import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiGet, apiPost, ApiError, CLAVE_ACCESS, CLAVE_REFRESH } from '../api/client'
import type { AuthUser, LoginResponse, RolUsuario } from '../api/types'
import { solicitarIdTokenDeGoogle } from './google'

type EstadoSesion = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  user: AuthUser | null
  roles: RolUsuario[]
  status: EstadoSesion
  loginWithPassword: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

// Re-exportado para que las pantallas que consumen useAuth puedan distinguir
// errores de credenciales (400) sin importar directamente de api/client.
export { ApiError }

function persistirSesion(data: LoginResponse) {
  if (!import.meta.env.PROD) {
    localStorage.setItem(CLAVE_ACCESS, data.access)
    localStorage.setItem(CLAVE_REFRESH, data.refresh)
  }
}

function limpiarSesion() {
  localStorage.removeItem(CLAVE_ACCESS)
  localStorage.removeItem(CLAVE_REFRESH)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [status, setStatus] = useState<EstadoSesion>('loading')

  useEffect(() => {
    apiGet<AuthUser>('/api/auth/user/')
      .then((data) => {
        setUser(data)
        setStatus('authenticated')
      })
      .catch(() => setStatus('unauthenticated'))
  }, [])

  async function loginWithPassword(email: string, password: string) {
    const data = await apiPost<LoginResponse>('/api/auth/login/', { email, password })
    persistirSesion(data)
    setUser(data.user)
    setStatus('authenticated')
  }

  async function loginWithGoogle() {
    const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID
    const idToken = await solicitarIdTokenDeGoogle(clientId)
    const data = await apiPost<LoginResponse>('/api/auth/google/', { id_token: idToken })
    persistirSesion(data)
    setUser(data.user)
    setStatus('authenticated')
  }

  async function logout() {
    try {
      await apiPost('/api/auth/logout/', {})
    } catch {
      // el logout limpia el lado del cliente igual aunque el request falle
    }
    limpiarSesion()
    setUser(null)
    setStatus('unauthenticated')
  }

  // `roles` se deriva de `user` en vez de guardarse aparte: hay una sola
  // fuente de verdad. El `?? []` es el ÚNICO punto del frontend que tolera
  // que el backend todavía no mande el campo (Task 3 del plan del paso 4);
  // gracias a él ningún consumidor necesita defenderse por su cuenta.
  const roles = user?.roles ?? []

  return (
    <AuthContext.Provider
      value={{ user, roles, status, loginWithPassword, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return context
}
