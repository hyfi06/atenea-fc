import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

interface TarjetaAsesoriaProps {
  asesoria: Asesoria
  nombreMateria: string
  indice: number
}

export function TarjetaAsesoria({ asesoria, nombreMateria, indice }: TarjetaAsesoriaProps) {
  const navigate = useNavigate()
  const fecha = FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))

  return (
    <li
      className="entrada-lista"
      style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}
    >
      <button
        type="button"
        onClick={() => navigate(`/asesorias/${asesoria.id}`)}
        className="flex w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
      >
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-on-surface">{nombreMateria}</span>
          <span className="text-xs text-on-surface-variant">
            {fecha} · {asesoria.hora_inicio.slice(0, 5)} · Alumno #{asesoria.alumno}
          </span>
        </div>
        <InsigniaEstado estado={asesoria.estado} />
      </button>
    </li>
  )
}
