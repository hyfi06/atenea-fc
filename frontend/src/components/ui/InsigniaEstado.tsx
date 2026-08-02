import type { EstadoAsesoria } from '../../api/types'

const ESTILOS: Record<EstadoAsesoria, string> = {
  agendada: 'bg-primary-container text-on-primary-container',
  realizada: 'bg-tertiary-container text-on-tertiary-container',
  cancelada: 'bg-error-container text-on-error-container',
}

const ETIQUETAS: Record<EstadoAsesoria, string> = {
  agendada: 'Agendada',
  realizada: 'Realizada',
  cancelada: 'Cancelada',
}

export function InsigniaEstado({ estado }: { estado: EstadoAsesoria }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${ESTILOS[estado]}`}>
      {ETIQUETAS[estado]}
    </span>
  )
}
