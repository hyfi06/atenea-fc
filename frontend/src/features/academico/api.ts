import { useQuery } from '@tanstack/react-query'
import { apiGet, ApiError } from '../../api/client'
import type { PeriodoVigente } from '../../api/types'

/**
 * Detalle del periodo vigente. El 404 (la SAE no ha dado de alta el semestre)
 * es una respuesta esperada, no un fallo: se deja pasar como error de la query
 * y quien la consume lo trata como "sin periodo". Sin reintentos, para no
 * insistir sobre un 404 que no va a cambiar en esta sesión.
 */
export function usePeriodoVigente() {
  return useQuery({
    queryKey: ['academico', 'periodo-vigente'],
    queryFn: () => apiGet<PeriodoVigente>('/api/academico/periodo-vigente/'),
    retry: (_conteo, error) => !(error instanceof ApiError && error.status === 404),
    staleTime: 5 * 60 * 1000,
  })
}

/** Si hoy se puede crear el RegistroAsesor del semestre vigente. Sin periodo
 *  dado de alta responde `false`, igual que el backend. */
export function useRegistroAsesoresAbierto(): boolean {
  const { data } = usePeriodoVigente()
  return data?.registro_asesores_abierto === true
}
