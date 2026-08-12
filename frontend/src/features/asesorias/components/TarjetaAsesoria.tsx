import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { useEsAsesor } from '../../../auth/rol'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

/** Lo mínimo que la tarjeta necesita: lo cumplen `Asesoria` y `AsesoriaAdmin`.
 *  `notas` se conserva en la forma aunque la tarjeta ya no lo renderice: en
 *  modo admin la sesión completa viaja en el router state al detalle SAE, que
 *  es quien muestra las notas. */
export type AsesoriaEnTarjeta = Pick<
  Asesoria,
  'id' | 'estado' | 'fecha' | 'hora_inicio' | 'alumno_nombre' | 'asesor_nombre' | 'notas'
>

interface TarjetaAsesoriaProps {
  asesoria: AsesoriaEnTarjeta
  nombreMateria: string
  indice: number
  /** Resalta y enfoca la tarjeta recién agendada (post-agendado). */
  destacar?: boolean
  /** Modo SAE: ambos nombres, sin notas, y navega al detalle read-only. */
  admin?: boolean
}

export function TarjetaAsesoria({
  asesoria,
  nombreMateria,
  indice,
  destacar = false,
  admin = false,
}: TarjetaAsesoriaProps) {
  const navigate = useNavigate()
  const esAsesor = useEsAsesor()
  const ref = useRef<HTMLElement | null>(null)
  const fecha = FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))

  // El asesor ve al alumno; el alumno ve al asesor. El SAE ve a los dos.
  const contraparte = esAsesor ? asesoria.alumno_nombre : asesoria.asesor_nombre
  const hora = asesoria.hora_inicio.slice(0, 5)
  const secundaria = admin
    ? `${fecha} · ${hora} · ${asesoria.alumno_nombre} · ${asesoria.asesor_nombre}`
    : `${fecha} · ${hora} · ${contraparte}`

  // El destino depende del MODO, no del rol: un miembro SAE que además sea
  // asesor no debe caer en el detalle del asesor, que monta mutaciones.
  const interactiva = admin || esAsesor

  // El detalle SAE no tiene endpoint propio y el listado admin está cacheado
  // por combinación de filtros: la sesión viaja en el router state para que el
  // detalle no dependa de qué query la trajo (próximas vs. un semestre).
  const irAlDetalle = () => {
    if (admin) {
      navigate(`/sae/asesorias/${asesoria.id}`, { state: { asesoria, nombreMateria } })
    } else {
      navigate(`/asesorias/${asesoria.id}`)
    }
  }

  useEffect(() => {
    if (destacar && ref.current) {
      ref.current.scrollIntoView({ block: 'center' })
      ref.current.focus()
    }
  }, [destacar])

  const contenido = (
    <div className="flex w-full items-center justify-between gap-3">
      <div className="flex min-w-0 flex-col gap-1">
        <span className="text-sm font-medium text-on-surface">{nombreMateria}</span>
        <span className="text-xs text-on-surface-variant">{secundaria}</span>
      </div>
      <InsigniaEstado estado={asesoria.estado} />
    </div>
  )

  const clasesBase = `flex w-full rounded-lg bg-surface-container px-4 py-3 text-left${destacar ? ' pulso-exito' : ''}`

  return (
    <li className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
      {interactiva ? (
        <button
          ref={(el) => { ref.current = el }}
          type="button"
          onClick={irAlDetalle}
          className={`foco-visible ${clasesBase}`}
        >
          {contenido}
        </button>
      ) : (
        // tabIndex=-1 permite el focus programático de `destacar` sin meterla
        // en el orden de tabulación.
        <div ref={(el) => { ref.current = el }} tabIndex={-1} className={`foco-visible ${clasesBase}`}>
          {contenido}
        </div>
      )}
    </li>
  )
}
