// Forma exacta de `accounts.serializers.UserDetailsSerializer` del backend.
// El mismo objeto alimenta GET /api/auth/user/ y la clave `user` del body de
// POST /api/auth/login/ y POST /api/auth/google/.
export type RolUsuario = 'alumno' | 'academico' | 'asesor_academico'  | 'sae'

export interface PerfilAlumno {
  id: number
  numero_cuenta: string
  carrera: number
  carrera_nombre: string
  generacion: number
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
  registro: number
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
  // (ADR 0021). Ninguna pantalla del alumno la lee; sólo DetalleAsesoria
  // (asesor-only) la consume.
  notas: string
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
