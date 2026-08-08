import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPatch, apiDelete } from '../../api/client'
import type { RegistroAsesor, Disponibilidad, Asesoria } from '../../api/types'
import { semestreActual } from './logica'

export function useMisRegistros() {
  return useQuery({
    queryKey: ['registros'],
    queryFn: () => apiGet<RegistroAsesor[]>('/api/asesorias/registros/'),
  })
}

/**
 * El registro de asesor del semestre pedido (el en curso por default).
 * Las dos pantallas de disponibilidad ("Mis materias" y "Mi horario") lo
 * necesitan igual, así que la búsqueda vive aquí y no en cada una.
 */
export function useRegistroDelSemestre(semestre: string = semestreActual()) {
  const { data: registros, isPending } = useMisRegistros()
  return {
    registro: registros?.find((r) => r.semestre === semestre) ?? null,
    cargando: isPending,
  }
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

/**
 * Quita una materia del registro del asesor.
 *
 * Contrato definido en la task 8 del plan de backend
 * (`docs/superpowers/plans/2026-08-04-login-oauth-backend.md`): es POST y no
 * DELETE para no habilitar el método DELETE en un viewset que lo excluye a
 * propósito. Ese endpoint todavía no existe en la rama de backend actual.
 */
export function useQuitarMateria(registroId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (materiaId: number) =>
      apiPost<RegistroAsesor>(`/api/asesorias/registros/${registroId}/materias/quitar/`, {
        materia_id: materiaId,
      }),
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

export function useMisAsesorias() {
  return useQuery({
    queryKey: ['asesorias'],
    queryFn: () => apiGet<Asesoria[]>('/api/asesorias/asesorias/'),
  })
}

export function useCancelarAsesoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) =>
      apiPost<Asesoria>(`/api/asesorias/asesorias/${id}/cancelar/`, { motivo }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}

export function useMarcarAsistencia() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, asistio }: { id: number; asistio: boolean }) =>
      apiPost<Asesoria>(`/api/asesorias/asesorias/${id}/marcar_asistencia/`, { asistio }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}

export function useGuardarNotas() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, texto }: { id: number; texto: string }) =>
      apiPost<Asesoria>(`/api/asesorias/asesorias/${id}/notas/`, { texto }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}
