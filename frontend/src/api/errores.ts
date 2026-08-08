import { ApiError } from './client'

/**
 * Primer mensaje legible de un error de la API.
 *
 * El backend traduce las reglas de negocio que viven en el modelo a
 * `400 {"detail": ["mensaje"]}` — una lista, aun con un solo mensaje — y los
 * errores de permiso a `{"detail": "mensaje"}`. Esta función absorbe las dos
 * formas y garantiza que la UI siempre tenga algo que mostrar.
 */
export function primerMensajeDeError(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: string[] | string } | null
    if (Array.isArray(body?.detail) && body.detail.length > 0) return body.detail[0]
    if (typeof body?.detail === 'string') return body.detail
  }
  return 'Ocurrió un error inesperado.'
}
