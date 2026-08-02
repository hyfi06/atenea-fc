import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPatch, apiDelete } from '../../api/client'
import type { RegistroAsesor, Disponibilidad } from '../../api/types'

export function useMisRegistros() {
  return useQuery({
    queryKey: ['registros'],
    queryFn: () => apiGet<RegistroAsesor[]>('/api/asesorias/registros/'),
  })
}

export function useCrearRegistro() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (semestre: string) => apiPost<RegistroAsesor>('/api/asesorias/registros/', { semestre }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['registros'] }),
  })
}

export function useAgregarMateria(registroId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (materiaId: number) =>
      apiPost<RegistroAsesor>(`/api/asesorias/registros/${registroId}/materias/`, { materia_id: materiaId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['registros'] }),
  })
}

export function useMisDisponibilidades() {
  return useQuery({
    queryKey: ['disponibilidades'],
    queryFn: () => apiGet<Disponibilidad[]>('/api/asesorias/disponibilidades/'),
  })
}

export function useCrearDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: Omit<Disponibilidad, 'id' | 'activa'>) =>
      apiPost<Disponibilidad>('/api/asesorias/disponibilidades/', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['disponibilidades'] }),
  })
}

export function useActualizarDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, activa }: { id: number; activa: boolean }) =>
      apiPatch<Disponibilidad>(`/api/asesorias/disponibilidades/${id}/`, { activa }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['disponibilidades'] }),
  })
}

export function useEliminarDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => apiDelete(`/api/asesorias/disponibilidades/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['disponibilidades'] }),
  })
}
