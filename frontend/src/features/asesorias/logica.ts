import type { Disponibilidad } from '../../api/types'

export function semestreActual(hoy: Date = new Date()): string {
  const anio = hoy.getFullYear()
  const numero = hoy.getMonth() < 6 ? '1' : '2'
  return `${anio}${numero}`
}

export function claveSlot(diaSemana: number, horaInicio: string): string {
  return `${diaSemana}-${horaInicio}`
}

export function mapaDisponibilidades(disponibilidades: Disponibilidad[]): Map<string, Disponibilidad> {
  const mapa = new Map<string, Disponibilidad>()
  for (const disponibilidad of disponibilidades) {
    if (disponibilidad.activa) {
      mapa.set(claveSlot(disponibilidad.dia_semana, disponibilidad.hora_inicio), disponibilidad)
    }
  }
  return mapa
}
