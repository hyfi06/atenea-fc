import { apiPost } from '../api/client'

/** Forma de la respuesta de los dos endpoints de reset de dj-rest-auth. */
export interface RespuestaDetalle {
  detail: string
}

/** `POST /api/auth/password/reset/`.
 *
 *  Responde 200 aunque el correo no exista o pertenezca a una cuenta que solo
 *  entra por Google: la respuesta es deliberadamente indistinguible (no
 *  enumeración). La UI no puede —ni debe— decir si el correo existe.
 *  Rate limit dedicado: 3/hour por IP; agotarlo devuelve 429. */
export function solicitarResetDePassword(email: string): Promise<RespuestaDetalle> {
  return apiPost<RespuestaDetalle>('/api/auth/password/reset/', { email })
}

/** `POST /api/auth/password/reset/confirm/`. Rate limit dedicado: 10/hour.
 *
 *  Se mandan las dos contraseñas tal cual las escribió el usuario: el backend
 *  valida que coincidan y que pasen los AUTH_PASSWORD_VALIDATORS, y devuelve el
 *  mensaje ya traducido. */
export function confirmarResetDePassword(datos: {
  uid: string
  token: string
  password1: string
  password2: string
}): Promise<RespuestaDetalle> {
  return apiPost<RespuestaDetalle>('/api/auth/password/reset/confirm/', {
    uid: datos.uid,
    token: datos.token,
    new_password1: datos.password1,
    new_password2: datos.password2,
  })
}
