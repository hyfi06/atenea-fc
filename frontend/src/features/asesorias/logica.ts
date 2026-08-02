import type { Disponibilidad, Asesoria } from '../../api/types'

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
