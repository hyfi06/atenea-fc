import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { useEsAsesor } from '../../../auth/rol'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

/** Lo mínimo que la tarjeta necesita: lo cumplen `Asesoria` y `AsesoriaAdmin`. */
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
  /** Modo SAE: ambos nombres + `notas`, y nunca navega a detalle. */
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
  const notas = admin ? asesoria.notas.trim() : ''

  // El detalle /asesorias/:id es asesor-only; en modo admin no hay ruta de
  // detalle en esta fase (spec §Out of scope), así que la tarjeta es estática.
  const interactiva = esAsesor && !admin

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
        {notas !== '' && <span className="text-xs text-on-surface-variant">Notas: {notas}</span>}
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
          onClick={() => navigate(`/asesorias/${asesoria.id}`)}
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
