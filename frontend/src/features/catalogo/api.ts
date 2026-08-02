import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../api/client'
import type { Materia, Carrera } from '../../api/types'

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: () => apiGet<Materia[]>('/api/materias/materias/'),
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
