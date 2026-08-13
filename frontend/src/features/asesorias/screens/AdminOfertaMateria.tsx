import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAsesoresDeMateria, useDisponibilidadDeAsesor } from '../api'
import { agruparPorDia } from '../logica'
import { useMapaMaterias } from '../../catalogo/api'
import { Skeleton } from '../../../components/ui/Skeleton'
import type { AsesorDisponible } from '../../../api/types'

const FORMATEADOR_DIA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })

/**
 * Consulta de oferta del SAE: materia → asesores → disponibilidad, sin
 * agendar. Reusa los mismos endpoints que el wizard del alumno (ampliados a
 * `EsAlumnoOMiembroSAE`, ADR 0023) y termina en visualización.
 */
export function AdminOfertaMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const idMateria = Number(materiaId)
  const navigate = useNavigate()
  const mapaMaterias = useMapaMaterias()

  const { data: asesores = [], isPending: cargandoAsesores } = useAsesoresDeMateria(
    Number.isInteger(idMateria) ? idMateria : null,
  )
  const [registroId, setRegistroId] = useState<number | null>(null)
  const { data: slots = [], isPending: cargandoSlots } = useDisponibilidadDeAsesor(
    registroId !== null ? idMateria : null,
    registroId,
  )
  const dias = useMemo(() => agruparPorDia(slots), [slots])

  const volver = (
    <button
      type="button"
      onClick={() => navigate('/sae/asesorias/oferta')}
      className="foco-visible w-fit min-h-11 text-sm text-primary"
    >
      ← Volver a la oferta
    </button>
  )

  if (!Number.isInteger(idMateria)) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        {volver}
        <p className="text-sm text-on-surface-variant">Materia inválida.</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      {volver}
      <h1 className="text-lg font-semibold text-on-background">
        {mapaMaterias.get(idMateria)?.nombre ?? `Materia #${idMateria}`}
      </h1>

      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium text-on-surface">Asesores</h2>
        {cargandoAsesores ? (
          <Skeleton className="h-14" />
        ) : asesores.length === 0 ? (
          <p className="text-sm text-on-surface-variant">Esta materia no tiene asesores disponibles.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {asesores.map((a) => (
              <li key={a.registro_id}>
                <BotonAsesor
                  asesor={a}
                  seleccionado={registroId === a.registro_id}
                  onClick={() => setRegistroId(a.registro_id)}
                />
              </li>
            ))}
          </ul>
        )}
      </section>

      {registroId !== null && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Disponibilidad</h2>
          {cargandoSlots ? (
            <Skeleton className="h-14" />
          ) : dias.length === 0 ? (
            <p className="text-sm text-on-surface-variant">
              Este asesor no tiene horarios en las próximas dos semanas.
            </p>
          ) : (
            <ul className="flex flex-col gap-3">
              {dias.map((d) => (
                <li key={d.fecha} className="flex flex-col gap-1">
                  <span className="text-sm text-on-surface">
                    {FORMATEADOR_DIA.format(new Date(`${d.fecha}T00:00:00`))}
                  </span>
                  <ul className="flex flex-wrap gap-2">
                    {d.slots.map((s) => (
                      <li
                        key={s.disponibilidad_id}
                        className="flex min-h-11 items-center rounded-full bg-surface-container px-3 text-xs text-on-surface-variant"
                      >
                        {s.hora_inicio.slice(0, 5)}–{s.hora_fin.slice(0, 5)} ·{' '}
                        {s.formato === 'virtual' ? 'Virtual' : s.ubicacion || 'Presencial'}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  )
}

function BotonAsesor({
  asesor,
  seleccionado,
  onClick,
}: {
  asesor: AsesorDisponible
  seleccionado: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-pressed={seleccionado}
      onClick={onClick}
      className={`foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg px-4 py-3 text-left ${
        seleccionado ? 'bg-primary-container text-on-primary-container' : 'bg-surface-container'
      }`}
    >
      <span className="text-sm font-medium">{asesor.asesor_nombre}</span>
      <span className="text-xs text-on-surface-variant">
        {asesor.area_nombre} · {asesor.formatos.map((f) => (f === 'virtual' ? 'Virtual' : 'Presencial')).join(' / ')}
      </span>
    </button>
  )
}
