import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { apiGet, apiPost, apiPatch, apiDelete } from '../../api/client'
import type {
  RegistroAsesor, Disponibilidad, Asesoria, SesionesFuturas,
  MateriaOferta, AsesorDisponible, SlotDisponibilidad, EstadoAsesoria,
  AsesoriaAdmin, AsesorDirectorio, AsesorDetalle, AlumnoBusqueda, AsesorBusqueda,
  PerfilAsesorAcademico,
} from '../../api/types'
import { semestreActual } from './logica'

/**
 * `habilitado` permite montar las pantallas del asesor en modo consulta
 * (SAE) sin disparar GET /registros/, que para un no-asesor sería 403.
 */
export function useMisRegistros(habilitado: boolean = true) {
  return useQuery({
    queryKey: ['registros'],
    queryFn: () => apiGet<RegistroAsesor[]>('/api/asesorias/registros/'),
    enabled: habilitado,
  })
}

/**
 * El registro de asesor del semestre pedido (el en curso por default).
 * Las dos pantallas de disponibilidad ("Mis materias" y "Mi horario") lo
 * necesitan igual, así que la búsqueda vive aquí y no en cada una.
 */
export function useRegistroDelSemestre(semestre: string = semestreActual(), habilitado: boolean = true) {
  const { data: registros, isPending } = useMisRegistros(habilitado)
  return {
    registro: registros?.find((r) => r.semestre === semestre) ?? null,
    // Con `enabled: false` TanStack Query reporta `isPending` para siempre;
    // apagada, la query no está cargando nada.
    cargando: habilitado && isPending,
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

export function useMisDisponibilidades(habilitado: boolean = true) {
  return useQuery({
    queryKey: ['disponibilidades'],
    queryFn: () => apiGet<Disponibilidad[]>('/api/asesorias/disponibilidades/'),
    enabled: habilitado,
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

/**
 * Sesiones agendadas a futuro sobre un bloque. Se consulta al abrir el
 * diálogo del bloque, para saber si desactivarlo requiere la advertencia de
 * 3 opciones. `enabled` evita la petición mientras no hay bloque abierto.
 *
 * Contrato de la task 6 del plan de backend; todavía no existe en
 * dev-backend.
 */
export function useSesionesFuturas(disponibilidadId: number | null) {
  return useQuery({
    queryKey: ['disponibilidades', disponibilidadId, 'sesiones-futuras'],
    queryFn: () =>
      apiGet<SesionesFuturas>(`/api/asesorias/disponibilidades/${disponibilidadId}/sesiones-futuras/`),
    enabled: disponibilidadId !== null,
    staleTime: 0,
  })
}

/**
 * Desactiva un bloque, con o sin cancelar sus sesiones futuras.
 *
 * Las dos opciones del modal de advertencia se sirven con un solo endpoint
 * distinguido por `cancelar_sesiones` (task 7 del plan de backend), así que
 * aquí también son una sola mutación. Invalida `asesorias` además de
 * `disponibilidades` porque la variante que cancela cambia las dos listas.
 */
export function useDesactivarDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, cancelarSesiones, motivo = '' }: { id: number; cancelarSesiones: boolean; motivo?: string }) =>
      apiPost<{ disponibilidad: Disponibilidad; sesiones_canceladas: number }>(
        `/api/asesorias/disponibilidades/${id}/desactivar/`,
        { cancelar_sesiones: cancelarSesiones, motivo },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['disponibilidades'] })
      queryClient.invalidateQueries({ queryKey: ['asesorias'] })
    },
  })
}

export function useOferta() {
  return useQuery({
    queryKey: ['oferta'],
    queryFn: () => apiGet<MateriaOferta[]>('/api/asesorias/oferta/'),
  })
}

export function useAsesoresDeMateria(materiaId: number | null) {
  return useQuery({
    queryKey: ['oferta', materiaId, 'asesores'],
    queryFn: () => apiGet<AsesorDisponible[]>(`/api/asesorias/oferta/${materiaId}/asesores/`),
    enabled: materiaId !== null,
  })
}

export function useDisponibilidadDeAsesor(materiaId: number | null, registroId: number | null) {
  return useQuery({
    queryKey: ['disponibilidad', materiaId, registroId],
    queryFn: () =>
      apiGet<SlotDisponibilidad[]>(
        `/api/asesorias/disponibilidad/buscar/?materia=${materiaId}&asesor=${registroId}`,
      ),
    enabled: materiaId !== null && registroId !== null,
  })
}

export interface PayloadAgendar {
  disponibilidad: number
  fecha: string
  materia: number
  carrera: number
}

export function useAgendarAsesoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PayloadAgendar) => apiPost<Asesoria>('/api/asesorias/asesorias/', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}

export function useSemestres() {
  return useQuery({
    queryKey: ['asesorias', 'semestres'],
    queryFn: () => apiGet<string[]>('/api/asesorias/asesorias/semestres/'),
  })
}

/** Sesiones filtradas por semestre para los subtabs del historial. La key
 *  comparte el prefijo ['asesorias'], así que `useAgendarAsesoria` la
 *  invalida junto con la lista principal. */
export function useAsesoriasDeSemestre(semestre: string | null) {
  return useQuery({
    queryKey: ['asesorias', { semestre }],
    queryFn: () => apiGet<Asesoria[]>(`/api/asesorias/asesorias/?semestre=${semestre}`),
    enabled: semestre !== null,
  })
}

export interface FiltrosAdminAsesorias {
  asesor?: number | null
  alumno?: number | null
  semestre?: string | null
  estado?: EstadoAsesoria | null
}

/**
 * URL del listado admin. Los filtros nulos se omiten; sin ninguno, el
 * backend devuelve las próximas agendadas (ADR 0023).
 */
export function rutaAdminAsesorias(filtros: FiltrosAdminAsesorias = {}): string {
  const params = new URLSearchParams()
  if (filtros.asesor != null) params.set('asesor', String(filtros.asesor))
  if (filtros.alumno != null) params.set('alumno', String(filtros.alumno))
  if (filtros.semestre != null) params.set('semestre', filtros.semestre)
  if (filtros.estado != null) params.set('estado', filtros.estado)
  const query = params.toString()
  return query ? `/api/asesorias/admin/asesorias/?${query}` : '/api/asesorias/admin/asesorias/'
}

export function useAdminAsesorias(filtros: FiltrosAdminAsesorias = {}) {
  return useQuery({
    queryKey: ['admin', 'asesorias', filtros],
    queryFn: () => apiGet<AsesoriaAdmin[]>(rutaAdminAsesorias(filtros)),
  })
}

/** Todos los semestres del sistema con asesorías (distinto de `useSemestres`,
 *  que es por-usuario). Alimenta los subtabs del histórico admin. */
export function useAdminSemestres() {
  return useQuery({
    queryKey: ['admin', 'semestres'],
    queryFn: () => apiGet<string[]>('/api/asesorias/admin/semestres/'),
  })
}

export function useAdminAsesores() {
  return useQuery({
    queryKey: ['admin', 'asesores'],
    queryFn: () => apiGet<AsesorDirectorio[]>('/api/asesorias/admin/asesores/'),
  })
}

/** Detalle read-only de un asesor. `semestre` nulo → el vigente (default del backend). */
export function useAdminAsesor(perfilId: number | null, semestre: string | null = null) {
  return useQuery({
    queryKey: ['admin', 'asesor', perfilId, semestre],
    queryFn: () =>
      apiGet<AsesorDetalle>(
        semestre === null
          ? `/api/asesorias/admin/asesores/${perfilId}/`
          : `/api/asesorias/admin/asesores/${perfilId}/?semestre=${semestre}`,
      ),
    enabled: perfilId !== null,
    // Entre semestres conserva el detalle previo para que no parpadee (M2).
    placeholderData: keepPreviousData,
  })
}

/** Autocompletar de alumno para el filtro de `AdminAsesorias`. */
export function useBuscarAlumnos(buscar: string) {
  return useQuery({
    queryKey: ['admin', 'alumnos', buscar],
    queryFn: () =>
      apiGet<AlumnoBusqueda[]>(`/api/asesorias/admin/alumnos/?buscar=${encodeURIComponent(buscar)}`),
    enabled: buscar.length >= 2,
  })
}

/** URL del autocompletar de asesores. Es el mismo endpoint del directorio
 *  (`useAdminAsesores`) con `?buscar=`; se extrae para poder testear la
 *  construcción de la query sin montar TanStack Query. */
export function rutaBuscarAsesores(buscar: string): string {
  return `/api/asesorias/admin/asesores/?buscar=${encodeURIComponent(buscar)}`
}

/** Autocompletar de asesor para el filtro de `AdminAsesorias`. Espejo de
 *  `useBuscarAlumnos`: busca por nombre o número de trabajador y sólo pega al
 *  servidor a partir de 2 caracteres. */
export function useBuscarAsesores(buscar: string) {
  return useQuery({
    queryKey: ['admin', 'asesores', 'buscar', buscar],
    queryFn: () => apiGet<AsesorBusqueda[]>(rutaBuscarAsesores(buscar)),
    enabled: buscar.length >= 2,
  })
}

/** Autoservicio de alta como asesor (ADR 0027 decisión 7). El perfil puede
 *  nacer inactivo: la vigencia la confirma un servicio externo. Quien la use
 *  debe llamar a `refrescarSesion()` de `useAuth` para que `roles` incluya
 *  `asesor_academico` sin recargar la página. */
export function useSolicitarSerAsesor() {
  return useMutation({
    mutationFn: (areaId: number) =>
      apiPost<PerfilAsesorAcademico>('/api/asesorias/asesores/solicitud/', { area: areaId }),
  })
}
