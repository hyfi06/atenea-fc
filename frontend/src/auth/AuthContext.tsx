import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiGet, apiPost, ApiError, CLAVE_ACCESS, CLAVE_REFRESH } from '../api/client'
import type { AuthUser, LoginResponse } from '../api/types'
import { solicitarAccessTokenDeGoogle } from './google'

type EstadoSesion = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  user: AuthUser | null
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
    const accessToken = await solicitarAccessTokenDeGoogle(clientId)
    const data = await apiPost<LoginResponse>('/api/auth/google/', { access_token: accessToken })
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

  return (
    <AuthContext.Provider value={{ user, status, loginWithPassword, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return context
}
