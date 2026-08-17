import { useAuth } from './AuthContext'

/**
 * El rol viene con el propio login: `GET /api/auth/user/` y la clave `user`
 * del body de `/api/auth/login/` y `/api/auth/google/` comparten serializer
 * en el backend, así que `roles` ya está en el contexto de auth.
 *
 * Esto reemplaza el sondeo que había aquí (pedir `GET /api/asesorias/registros/`
 * y leer 200 vs 403), que era el workaround 1 de la deuda técnica 0010: no
 * escalaba a más de un rol sin una petición extra por cada rol a verificar.
 */
export function useEsAsesor(): boolean {
  // `asesor_academico` aparece aunque el perfil esté inactivo — mismo criterio
  // que la permission class EsAsesorAcademico, que solo comprueba existencia.
  return useAuth().roles.includes('asesor_academico')
}

export function useEsAlumno(): boolean {
  return useAuth().roles.includes('alumno')
}

/**
 * Miembro de la SAE (ADR 0023): el backend deriva el rol de la existencia de
 * `PerfilSAE`, igual que los demás roles. Habilita el área `/sae/*`.
 */
export function useEsMiembroSAE(): boolean {
  return useAuth().roles.includes('sae')
}

/**
 * Académico (ADR 0012: existe `PerfilAcademico`). Es distinto de `useEsAsesor`:
 * un académico sin `PerfilAsesorAcademico` todavía no es asesor, y este hook es
 * lo único que le permite descubrir que puede registrarse (ADR 0027 decisión 9).
 */
export function useEsAcademico(): boolean {
  return useAuth().roles.includes('academico')
}