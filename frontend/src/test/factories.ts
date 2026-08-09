import type { AuthUser } from '../api/types'

/**
 * Usuario con la forma exacta que devuelve `GET /api/auth/user/` y que viaja
 * en la clave `user` del body de login (mismo serializer del lado del
 * backend). Vive fuera de los archivos `.test.tsx` a propósito: `tsconfig.app.json`
 * excluye los tests de `tsc -b`, así que este es el único lugar donde el
 * compilador verifica que la forma sigue cuadrando con `AuthUser`.
 */
export function usuarioDePrueba(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    pk: 1,
    email: 'usuaria@ciencias.unam.mx',
    first_name: 'Ana',
    apellido1: 'López',
    apellido2: 'Ruiz',
    nombre_completo: 'Ana López Ruiz',
    roles: [],
    perfil_alumno: null,
    perfil_academico: null,
    perfil_asesor_academico: null,
    ...overrides,
  }
}
