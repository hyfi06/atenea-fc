import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../api/client'
import type { Materia, Carrera, RespuestaPaginada } from '../../api/types'

const RUTA_MATERIAS = '/api/materias/materias/'

export interface ParametrosRutaMaterias {
  /** `null` = todas las carreras. */
  carrera?: number | null
  /** Cadena vacía = sin búsqueda; viaja como `?search=` al backend. */
  search?: string
  habilitada_asesorias?: boolean
  /** 1-indexado. La página 1 se omite de la URL. */
  page?: number
}

/**
 * Arma la ruta del catálogo paginado. Vive aquí y no en `api/client.ts`: por
 * ahora este es el único endpoint paginado del proyecto, generalizar `apiGet`
 * es prematuro.
 */
export function construirRutaMaterias(params: ParametrosRutaMaterias = {}): string {
  const query = new URLSearchParams()
  if (params.habilitada_asesorias !== undefined) {
    query.set('habilitada_asesorias', params.habilitada_asesorias ? '1' : '0')
  }
  if (params.carrera !== undefined && params.carrera !== null) {
    query.set('carrera', String(params.carrera))
  }
  if (params.search !== undefined && params.search !== '') {
    query.set('search', params.search)
  }
  if (params.page !== undefined && params.page > 1) {
    query.set('page', String(params.page))
  }
  const cadena = query.toString()
  return cadena === '' ? RUTA_MATERIAS : `${RUTA_MATERIAS}?${cadena}`
}

/**
 * Recorre todas las páginas del catálogo y devuelve el array completo.
 *
 * Existe para que `useMaterias()` siga cumpliendo el contrato que asumen sus
 * consumidores de lookup (`useMapaMaterias`), que necesitan el catálogo entero
 * en memoria. Cuesta N requests secuenciales en vez de 1 — deuda 0022.
 */
export async function obtenerTodasLasMaterias(): Promise<Materia[]> {
  const materias: Materia[] = []
  let pagina = 1
  let hayMas = true
  while (hayMas) {
    const respuesta = await apiGet<RespuestaPaginada<Materia>>(
      construirRutaMaterias({ page: pagina }),
    )
    materias.push(...respuesta.results)
    hayMas = respuesta.next !== null
    pagina += 1
  }
  return materias
}

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: obtenerTodasLasMaterias,
    staleTime: Infinity,
  })
}

export function useCarreras() {
  return useQuery({
    queryKey: ['carreras'],
    queryFn: () => apiGet<Carrera[]>('/api/carreras/carreras/'),
    staleTime: Infinity,
  })
}

export function useMapaMaterias(): Map<number, Materia> {
  const { data } = useMaterias()
  return useMemo(() => new Map((data ?? []).map((materia) => [materia.id, materia])), [data])
}

export function useMapaCarreras(): Map<number, Carrera> {
  const { data } = useCarreras()
  return useMemo(() => new Map((data ?? []).map((carrera) => [carrera.id, carrera])), [data])
}
