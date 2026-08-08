import type { Disponibilidad, Asesoria } from '../../api/types'

export function semestreActual(hoy: Date = new Date()): string {
  const anio = hoy.getFullYear()
  const numero = hoy.getMonth() < 6 ? '1' : '2'
  return `${anio}${numero}`
}

export function claveSlot(diaSemana: number, horaInicio: string): string {
  return `${diaSemana}-${horaInicio}`
}

function claveOrden(asesoria: Asesoria): string {
  return `${asesoria.fecha}T${asesoria.hora_inicio}`
}

export function proximas(asesorias: Asesoria[]): Asesoria[] {
  return asesorias
    .filter((a) => a.estado === 'agendada')
    .sort((a, b) => claveOrden(a).localeCompare(claveOrden(b)))
}

export function historial(asesorias: Asesoria[]): Asesoria[] {
  return asesorias
    .filter((a) => a.estado !== 'agendada')
    .sort((a, b) => claveOrden(b).localeCompare(claveOrden(a)))
}

export function sesionesPreviasConNotas(asesorias: Asesoria[], alumnoId: number, excluirId: number): Asesoria[] {
  return asesorias
    .filter((a) => a.alumno === alumnoId && a.id !== excluirId && a.estado === 'realizada' && a.notas.trim() !== '')
    .sort((a, b) => claveOrden(b).localeCompare(claveOrden(a)))
}

export function sesionYaOcurrio(asesoria: Pick<Asesoria, 'fecha' | 'hora_inicio'>, ahora: Date): boolean {
  const inicio = new Date(`${asesoria.fecha}T${asesoria.hora_inicio}`)
  return ahora >= inicio
}

export function puedeGuardarNotas(asesoria: Pick<Asesoria, 'estado' | 'asistio'>): boolean {
  return asesoria.estado === 'realizada' && asesoria.asistio === true
}

/** Los 28 slots de 30 minutos que cubre un día de asesorías: 07:00–20:30. */
export function horasDelDia(): string[] {
  const horas: string[] = []
  for (let h = 7; h <= 20; h++) {
    horas.push(`${String(h).padStart(2, '0')}:00:00`)
    horas.push(`${String(h).padStart(2, '0')}:30:00`)
  }
  return horas
}

export interface SlotHorario {
  hora: string
  clave: string
  /** La disponibilidad registrada en ese slot, activa o no. */
  disponibilidad: Disponibilidad | null
  activo: boolean
}

/**
 * Las 28 filas de un día para la pantalla "Mi horario".
 *
 * Distingue tres situaciones que la UI colapsa en dos chips: sin
 * disponibilidad, con una inactiva (se puede reactivar) y con una activa.
 * Por eso devuelve `disponibilidad` aunque `activo` sea `false` — sin ese
 * dato la pantalla no podría reactivar un bloque y trataría de crear uno
 * nuevo sobre un horario ya ocupado.
 */
export function slotsDelDia(diaSemana: number, disponibilidades: Disponibilidad[]): SlotHorario[] {
  const delDia = new Map<string, Disponibilidad>()
  for (const disponibilidad of disponibilidades) {
    if (disponibilidad.dia_semana === diaSemana) {
      delDia.set(disponibilidad.hora_inicio, disponibilidad)
    }
  }

  return horasDelDia().map((hora) => {
    const disponibilidad = delDia.get(hora) ?? null
    return {
      hora,
      clave: claveSlot(diaSemana, hora),
      disponibilidad,
      activo: disponibilidad?.activa === true,
    }
  })
}

/** Día de la semana de hoy en la convención del backend: 0 = lunes. */
export function diaSemanaHoy(hoy: Date = new Date()): number {
  return (hoy.getDay() + 6) % 7
}
