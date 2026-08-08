export interface AuthUser {
  pk: number
  email: string
  first_name: string
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
