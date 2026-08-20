const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export const CLAVE_ACCESS = 'atenea_access'
export const CLAVE_REFRESH = 'atenea_refresh'

/** Nombre default de la cookie CSRF de Django (`CSRF_COOKIE_NAME`). */
const COOKIE_CSRF = 'csrftoken'
/** Django solo valida CSRF en los métodos que no son seguros. */
const METODOS_SEGUROS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE'])

export class ApiError extends Error {
  status: number
  body: unknown
  constructor(status: number, body: unknown) {
    super(`API error ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function tokenDeAcceso(): string | null {
  return import.meta.env.PROD ? null : localStorage.getItem(CLAVE_ACCESS)
}

/** Lee una cookie legible por JS. La `csrftoken` de Django no es httpOnly a
 *  propósito: en prod (ADR 0018 + deuda 0009) el SPA tiene que reenviarla como
 *  header `X-CSRFToken` en toda escritura, porque el JWT viaja en cookie y
 *  `JWT_AUTH_COOKIE_USE_CSRF` está activo. */
export function leerCookie(nombre: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

function agregarCsrf(headers: Headers, metodo: string) {
  if (METODOS_SEGUROS.has(metodo.toUpperCase())) return
  const csrf = leerCookie(COOKIE_CSRF)
  if (csrf) headers.set('X-CSRFToken', csrf)
}

async function refrescarToken(): Promise<boolean> {
  const body = import.meta.env.PROD ? {} : { refresh: localStorage.getItem(CLAVE_REFRESH) }
  const headers = new Headers({ 'Content-Type': 'application/json' })
  agregarCsrf(headers, 'POST')
  const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify(body),
  })
  if (!response.ok) return false
  if (!import.meta.env.PROD) {
    const data = (await response.json()) as { access: string }
    localStorage.setItem(CLAVE_ACCESS, data.access)
  }
  return true
}

async function solicitar<T>(path: string, init: RequestInit = {}, permitirReintento = true): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  agregarCsrf(headers, init.method ?? 'GET')
  const token = tokenDeAcceso()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })

  if (response.status === 401 && permitirReintento) {
    const seRefresco = await refrescarToken()
    if (seRefresco) return solicitar<T>(path, init, false)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, body)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return solicitar<T>(path, { method: 'GET' })
}

export function apiPost<T>(path: string, data?: unknown): Promise<T> {
  return solicitar<T>(path, {
    method: 'POST',
    body: data !== undefined ? JSON.stringify(data) : undefined,
  })
}

export function apiPatch<T>(path: string, data: unknown): Promise<T> {
  return solicitar<T>(path, { method: 'PATCH', body: JSON.stringify(data) })
}

export function apiDelete(path: string): Promise<void> {
  return solicitar<void>(path, { method: 'DELETE' })
}
