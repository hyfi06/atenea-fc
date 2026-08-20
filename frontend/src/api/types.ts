// Forma exacta de `accounts.serializers.UserDetailsSerializer` del backend.
// El mismo objeto alimenta GET /api/auth/user/ y la clave `user` del body de
// POST /api/auth/login/ y POST /api/auth/google/.
export type RolUsuario = 'alumno' | 'academico' | 'asesor_academico'  | 'sae'

/** Una inscripción del alumno a una carrera. Espejo de `accounts.HistoriaAcademica`. */
export interface InscripcionAlumno {
  carrera: number
  carrera_nombre: string
  generacion: number
}

export interface PerfilAlumno {
  id: number
  numero_cuenta: string
  // Puede traer más de una fila: carrera simultánea o segunda carrera bajo el
  // mismo número de cuenta (ADR 0027 decisión 1). `correos_alternos` no viaja
  // aquí a propósito: es visible solo para la SAE.
  historial: InscripcionAlumno[]
}

export interface PerfilAcademico {
  id: number
  numero_trabajador: string
}

export interface PerfilAsesorAcademico {
  id: number
  area: number
  area_nombre: string
  // Ojo: `asesor_academico` aparece en `roles` aunque esto sea false — el rol
  // sigue el criterio de la permission class EsAsesorAcademico del backend,
  // que solo comprueba que el perfil exista.
  activo: boolean
}

export interface AuthUser {
  pk: number
  email: string
  first_name: string
  apellido1: string
  apellido2: string
  nombre_completo: string
  roles: RolUsuario[]
  perfil_alumno: PerfilAlumno | null
  perfil_academico: PerfilAcademico | null
  perfil_asesor_academico: PerfilAsesorAcademico | null
}

export interface LoginResponse {
  access: string
  refresh: string
  user: AuthUser
}

export interface Materia {
  id: number
  clave: string
  nombre: string
  carrera: number
  nivel: string | null
  plan: number
  habilitada_asesorias: boolean
}

export interface Carrera {
  id: number
  clave: number
  nombre: string
  area: { id: number; nombre: string }
  acepta_nuevo_ingreso: boolean
}

export interface RegistroAsesor {
  id: number
  semestre: string
  materias: number[]
}

export type FormatoAsesoria = 'presencial' | 'virtual'
export type EstadoAsesoria = 'agendada' | 'cancelada' | 'realizada'

export interface Disponibilidad {
  id: number
  // Opcional: el detalle admin (GET /admin/asesores/{id}/) no expone el
  // registro al que pertenece el bloque. Ninguna pantalla lee este campo;
  // sólo `useCrearDisponibilidad` lo envía.
  registro?: number
  dia_semana: number
  hora_inicio: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  activa: boolean
}

export interface Asesoria {
  id: number
  alumno: number
  alumno_nombre: string
  asesor_nombre: string
  disponibilidad: number
  materia: number
  carrera: number
  fecha: string
  hora_inicio: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  estado: EstadoAsesoria
  asistio: boolean | null
  // El backend omite `notas` cuando quien pide no es el asesor dueño
  // (ADR 0021): el campo viene ausente (`undefined`), no `''`, en esos
  // payloads. DetalleAsesoria es la única pantalla que la consume para
  // edición y debe normalizar con `?? ''` antes de leerla como string.
  notas?: string
  creado_en: string
}

/** Vista mínima de una asesoría agendada sobre un bloque de disponibilidad.
 *  Contrato de GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/. */
export interface SesionFutura {
  id: number
  fecha: string
  hora_inicio: string
  alumno_nombre: string
  materia_nombre: string
}

export interface SesionesFuturas {
  total: number
  sesiones: SesionFutura[]
}

export interface MateriaOferta {
  materia_id: number
  nombre: string
  carrera_id: number
  num_asesores: number
}

export interface AsesorDisponible {
  registro_id: number
  asesor_nombre: string
  area_nombre: string
  formatos: FormatoAsesoria[]
}

/** Resultado de GET /disponibilidad/buscar/?asesor=, extendido con la
 *  identidad del asesor (ADR 0021). */
export interface SlotDisponibilidad {
  registro_id: number
  asesor_nombre: string
  disponibilidad_id: number
  fecha: string
  hora_inicio: string
  hora_fin: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
}

/** Materia resuelta que devuelve el detalle admin de un asesor. */
export interface MateriaResumen {
  id: number
  clave: string
  nombre: string
}

/**
 * GET /api/asesorias/admin/asesorias/ — vista admin de una sesión.
 * A diferencia de `Asesoria`, expone ambos nombres y `notas` (el SAE sí las
 * ve, ADR 0023), y omite `alumno`, `disponibilidad` y `creado_en`.
 */
export interface AsesoriaAdmin {
  id: number
  estado: EstadoAsesoria
  fecha: string
  hora_inicio: string
  materia: number
  carrera: number
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  alumno_nombre: string
  asesor_nombre: string
  asistio: boolean | null
  notas: string
}

/** GET /api/asesorias/admin/asesores/ */
export interface AsesorDirectorio {
  perfil_id: number
  nombre: string
  // Vive en `accounts.PerfilAcademico`, no en el perfil de asesor: el backend
  // lo resuelve y manda "" cuando el asesor no tiene PerfilAcademico.
  numero_trabajador: string
  area_nombre: string
  activo: boolean
  num_materias_semestre_vigente: number
}

/** Subconjunto de `AsesorDirectorio` que consume el autocompletar del filtro
 *  de asesor. Espejo de `AlumnoBusqueda`: el endpoint es el mismo directorio
 *  con `?buscar=`, la pantalla sólo lee estos tres campos. */
export interface AsesorBusqueda {
  perfil_id: number
  nombre: string
  numero_trabajador: string
}

/** GET /api/asesorias/admin/asesores/{perfil_id}/?semestre= */
export interface AsesorDetalle {
  perfil_id: number
  nombre: string
  area_nombre: string
  activo: boolean
  semestre: string
  materias: MateriaResumen[]
  // El endpoint manda además `hora_fin`, que el frontend no usa.
  disponibilidades: Disponibilidad[]
}

/** GET /api/asesorias/admin/alumnos/?buscar= */
export interface AlumnoBusqueda {
  perfil_id: number
  nombre: string
  numero_cuenta: string
  /** Correos que la SAE conoce además del de login. Solo llega a endpoints SAE. */
  correos_alternos: string[]
}

/** GET /api/academico/periodo-vigente/. 404 = la SAE no dio de alta el semestre. */
export interface PeriodoVigente {
  semestre: string
  fecha_inicio: string
  fecha_fin: string
  registro_asesores_inicio: string
  registro_asesores_fin: string
  registro_asesores_abierto: boolean
}

/** GET /api/academico/periodo-vigente/. 404 = la SAE no dio de alta el semestre. */
export interface PeriodoVigente {
  semestre: string
  fecha_inicio: string
  fecha_fin: string
  registro_asesores_inicio: string
  registro_asesores_fin: string
  registro_asesores_abierto: boolean
}
