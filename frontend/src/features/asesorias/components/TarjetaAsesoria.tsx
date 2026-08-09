import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { useEsAsesor } from '../../../auth/rol'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

interface TarjetaAsesoriaProps {
  asesoria: Asesoria
  nombreMateria: string
  indice: number
  /** Resalta y enfoca la tarjeta recién agendada (post-agendado). */
  destacar?: boolean
}

export function TarjetaAsesoria({ asesoria, nombreMateria, indice, destacar = false }: TarjetaAsesoriaProps) {
  const navigate = useNavigate()
  const esAsesor = useEsAsesor()
  const ref = useRef<HTMLElement | null>(null)
  const fecha = FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))

  // El asesor ve al alumno; el alumno ve al asesor. Los dos nombres los
  // expone el serializer (ADR 0021); reemplaza el viejo `Alumno #{id}`.
  const contraparte = esAsesor ? asesoria.alumno_nombre : asesoria.asesor_nombre

  useEffect(() => {
    if (destacar && ref.current) {
      ref.current.scrollIntoView({ block: 'center' })
      ref.current.focus()
    }
  }, [destacar])

  const contenido = (
    <div className="flex w-full items-center justify-between">
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-on-surface">{nombreMateria}</span>
        <span className="text-xs text-on-surface-variant">
          {fecha} · {asesoria.hora_inicio.slice(0, 5)} · {contraparte}
        </span>
      </div>
      <InsigniaEstado estado={asesoria.estado} />
    </div>
  )

  const clasesBase = `flex w-full rounded-lg bg-surface-container px-4 py-3 text-left${destacar ? ' pulso-exito' : ''}`

  return (
    <li className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
      {esAsesor ? (
        <button
          ref={(el) => { ref.current = el }}
          type="button"
          onClick={() => navigate(`/asesorias/${asesoria.id}`)}
          className={`foco-visible ${clasesBase}`}
        >
          {contenido}
        </button>
      ) : (
        // El alumno no navega a detalle: /asesorias/:id es asesor-only
        // (spec §Out of scope). tabIndex=-1 permite el focus programático de
        // `destacar` sin meterla en el orden de tabulación.
        <div ref={(el) => { ref.current = el }} tabIndex={-1} className={clasesBase}>
          {contenido}
        </div>
      )}
    </li>
  )
}
