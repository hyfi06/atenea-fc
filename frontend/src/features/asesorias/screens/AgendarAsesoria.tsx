import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useDisponibilidadDeMateria, useAgendarAsesoria } from '../api'
import { agruparPorDia } from '../logica'
import { useAuth } from '../../../auth/AuthContext'
import { useMapaCarreras, useMapaMaterias } from '../../catalogo/api'
import { Dialogo } from '../../../components/ui/Dialogo'
import { Skeleton } from '../../../components/ui/Skeleton'
import { primerMensajeDeError } from '../../../api/errores'
import { ApiError } from '../../../api/client'
import type { SlotDisponibilidad } from '../../../api/types'

const FORMATEADOR_DIA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })

export function AgendarAsesoria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const idMateria = Number(materiaId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const mapaCarreras = useMapaCarreras()
  const mapaMaterias = useMapaMaterias()

  const { data: slots = [], isPending: cargandoSlots } = useDisponibilidadDeMateria(
    Number.isInteger(idMateria) ? idMateria : null,
  )
  const dias = useMemo(() => agruparPorDia(slots), [slots])

  const [fecha, setFecha] = useState<string | null>(null)
  const [slot, setSlot] = useState<SlotDisponibilidad | null>(null)
  const historial = user?.perfil_alumno?.historial ?? []
  // Con una sola inscripción no hay nada que preguntar: se preselecciona.
  // Con dos o más, `carrera` arranca en null y el backend exige el campo.
  const [carrera, setCarrera] = useState<number | null>(
    historial.length === 1 ? historial[0].carrera : null,
  )
  const [confirmando, setConfirmando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const agendar = useAgendarAsesoria()

  const paso = fecha === null ? 'dia' : slot === null ? 'bloque' : 'carrera'

  function volver() {
    setError(null)
    if (slot !== null) return setSlot(null)
    if (fecha !== null) return setFecha(null)
    navigate('/asesorias')
  }

  function confirmar() {
    if (slot === null || carrera === null || fecha === null) return
    agendar.mutate(
      { disponibilidad: slot.disponibilidad_id, fecha, materia: idMateria, carrera },
      {
        onSuccess: (asesoria) => {
          setConfirmando(false)
          navigate('/asesorias', { state: { nuevaAsesoriaId: asesoria.id } })
        },
        onError: (err) => {
          setConfirmando(false)
          if (err instanceof ApiError && err.status === 409) {
            // El bloque tomado sigue en la caché de disponibilidad (y `num_asesores`
            // en la oferta pudo cambiar); invalidar ambos fuerza el refetch al
            // regresar al paso de día y evita reofrecer el bloque ya ocupado.
            queryClient.invalidateQueries({ queryKey: ['disponibilidad'] })
            queryClient.invalidateQueries({ queryKey: ['oferta'] })
            setError('Ese horario ya fue tomado. Elige otro día.')
            setSlot(null)
            setFecha(null)
          } else {
            setError(primerMensajeDeError(err))
          }
        },
      },
    )
  }

  const slotsDelDia = dias.find((d) => d.fecha === fecha)?.slots ?? []

  if (!Number.isInteger(idMateria)) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate('/asesorias')} className="foco-visible w-fit min-h-11 text-sm text-primary">← Volver a Asesorías</button>
        <p className="text-sm text-on-surface-variant">Materia inválida.</p>
      </main>
    )
  }

  if (historial.length === 0) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate('/asesorias')} className="foco-visible w-fit min-h-11 text-sm text-primary">← Volver a Asesorías</button>
        <p className="text-sm text-on-surface-variant">Sólo los alumnos pueden agendar asesorías.</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={volver} className="foco-visible w-fit min-h-11 text-sm text-primary">← Atrás</button>
      <h1 className="text-lg font-semibold text-on-background">
        {mapaMaterias.get(idMateria)?.nombre ?? `Materia #${idMateria}`}
      </h1>

      {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}

      {paso === 'dia' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un día</h2>
          {cargandoSlots ? (
            <Skeleton className="h-14" />
          ) : dias.length === 0 ? (
            <p className="text-sm text-on-surface-variant">Esta materia no tiene horarios en las próximas dos semanas.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {dias.map((d, indice) => (
                <li key={d.fecha} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
                  <button
                    type="button"
                    onClick={() => setFecha(d.fecha)}
                    className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
                  >
                    <span className="text-sm text-on-surface">
                      {FORMATEADOR_DIA.format(new Date(`${d.fecha}T00:00:00`))}
                    </span>
                    <span className="text-xs text-on-surface-variant">
                      {d.slots.length} bloque{d.slots.length === 1 ? '' : 's'}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {paso === 'bloque' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un bloque</h2>
          <ul className="flex flex-col gap-2">
            {slotsDelDia.map((s) => (
              <li key={s.disponibilidad_id}>
                <button
                  type="button"
                  onClick={() => setSlot(s)}
                  className="fila-interactiva foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg bg-surface-container px-4 py-3 text-left"
                >
                  <span className="flex w-full items-center justify-between text-sm text-on-surface">
                    <span>{s.hora_inicio.slice(0, 5)}–{s.hora_fin.slice(0, 5)}</span>
                    <span className="text-xs text-on-surface-variant">
                      {s.formato === 'virtual' ? 'Virtual' : s.ubicacion || 'Presencial'}
                    </span>
                  </span>
                  <span className="text-xs text-on-surface-variant">{s.asesor_nombre}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {paso === 'carrera' && slot !== null && fecha !== null && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-on-surface">Confirma tu asesoría</h2>
          <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
            <dt>Día</dt>
            <dd>{FORMATEADOR_DIA.format(new Date(`${fecha}T00:00:00`))}</dd>
            <dt>Hora</dt>
            <dd>{slot.hora_inicio.slice(0, 5)}</dd>
            <dt>Asesor</dt>
            <dd>{slot.asesor_nombre}</dd>
          </dl>

          <div className="flex flex-col gap-1">
            <label htmlFor="carrera-agendar" className="text-xs text-on-surface-variant">Carrera</label>
            <select
              id="carrera-agendar"
              value={carrera ?? ''}
              onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
              className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
            >
              {historial.length > 1 && <option value="">Elige una carrera</option>}
              {historial.map((inscripcion) => (
                <option key={inscripcion.carrera} value={inscripcion.carrera}>
                  {mapaCarreras.get(inscripcion.carrera)?.nombre ?? inscripcion.carrera_nombre}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => setConfirmando(true)}
            disabled={carrera === null}
            className="foco-visible flex min-h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-on-primary disabled:opacity-60"
          >
            Continuar
          </button>

          <Dialogo
            abierto={confirmando}
            titulo="Confirmar asesoría"
            descripcion={`${FORMATEADOR_DIA.format(new Date(`${fecha}T00:00:00`))} · ${slot.hora_inicio.slice(0, 5)}`}
            onCerrar={() => setConfirmando(false)}
            acciones={[{ etiqueta: 'Agendar', cargando: agendar.isPending, onClick: confirmar }]}
          />
        </section>
      )}
    </main>
  )
}
