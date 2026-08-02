import { useQuery } from '@tanstack/react-query'
import { apiGet, ApiError } from '../api/client'
import type { RegistroAsesor } from '../api/types'

// Sondeo interino: no existe endpoint de perfil/rol (deuda técnica 0010).
// GET /api/asesorias/registros/ es exclusivo de EsAsesorAcademico — 200
// significa "es asesor", 403 significa "no lo es".
export function useEsAsesor() {
  return useQuery({
    queryKey: ['rol', 'asesor'],
    queryFn: async () => {
      try {
        await apiGet<RegistroAsesor[]>('/api/asesorias/registros/')
        return true
      } catch (error) {
        if (error instanceof ApiError && error.status === 403) return false
        throw error
      }
    },
    staleTime: 5 * 60 * 1000,
  })
}
