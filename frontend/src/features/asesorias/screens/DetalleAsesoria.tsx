import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useMisAsesorias, useCancelarAsesoria, useMarcarAsistencia, useGuardarNotas } from '../api'
import { useMapaMaterias, useMapaCarreras } from '../../catalogo/api'
import { sesionesPreviasConNotas, sesionYaOcurrio, puedeGuardarNotas } from '../logica'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { Skeleton } from '../../../components/ui/Skeleton'
import { Boton } from '../../../components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { DialogoCancelar } from '../components/DialogoCancelar'
import { ApiError } from '../../../api/client'
import type { Asesoria } from '../../../api/types'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
const FORMATEADOR_HORA = new Intl.DateTimeFormat('es-MX', { hour: '2-digit', minute: '2-digit' })

function primerMensajeDeError(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: string[] | string } | null
    if (Array.isArray(body?.detail)) return body.detail[0]
    if (typeof body?.detail === 'string') return body.detail
  }
  return 'Ocurrió un error inesperado.'
}

export function DetalleAsesoria() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()
  const mapaCarreras = useMapaCarreras()

  if (isPending) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24" />
      </main>
    )
  }

  const asesoria = asesorias.find((a) => a.id === Number(id))
  if (!asesoria) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <p className="text-sm text-on-surface-variant">No se encontró la asesoría.</p>
        <button type="button" onClick={() => navigate('/asesorias')} className="w-fit text-sm text-primary">
          ← Volver a Asesorías
        </button>
      </main>
    )
  }

  const previas = sesionesPreviasConNotas(asesorias, asesoria.alumno, asesoria.id)

  return (
    <main className="flex min-h-svh flex-col gap-6 px-6 py-6">
      <button type="button" onClick={() => navigate('/asesorias')} className="w-fit text-sm text-primary">
        ← Volver a Asesorías
      </button>

      <section className="rounded-lg bg-surface-container p-4">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-base font-semibold text-on-surface">
            {mapaMaterias.get(asesoria.materia)?.nombre ?? `Materia #${asesoria.materia}`}
          </h1>
          <InsigniaEstado estado={asesoria.estado} />
        </div>
        <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
          <dt>Alumno</dt>
          <dd>Alumno #{asesoria.alumno}</dd>
          <dt>Carrera</dt>
          <dd>{mapaCarreras.get(asesoria.carrera)?.nombre ?? `Carrera #${asesoria.carrera}`}</dd>
          <dt>Fecha</dt>
          <dd>{FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))}</dd>
          <dt>Hora</dt>
          <dd>{asesoria.hora_inicio.slice(0, 5)}</dd>
          <dt>Formato</dt>
          <dd>
            {asesoria.formato === 'virtual' ? (
              <a href={asesoria.liga_virtual} target="_blank" rel="noreferrer" className="text-primary underline">
                Liga de la sesión
              </a>
            ) : (
              asesoria.ubicacion
            )}
          </dd>
        </dl>
      </section>

      <SeccionAcciones asesoria={asesoria} />

      <section>
        <h2 className="mb-2 text-sm font-medium text-on-surface">Notas de sesiones anteriores con este alumno</h2>
        {previas.length === 0 ? (
          <p className="text-sm text-on-surface-variant">No hay notas de sesiones anteriores.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {previas.map((previa) => (
              <li key={previa.id} className="rounded-lg bg-surface-container-low p-3 text-sm">
                <p className="mb-1 text-xs text-on-surface-variant">
                  {FORMATEADOR_FECHA.format(new Date(`${previa.fecha}T00:00:00`))}
                </p>
                <p className="text-on-surface">{previa.notas}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}

function SeccionAcciones({ asesoria }: { asesoria: Asesoria }) {
  const { mensaje, mostrar } = useRetroalimentacion()
  const cancelar = useCancelarAsesoria()
  const marcarAsistencia = useMarcarAsistencia()
  const guardarNotas = useGuardarNotas()
  const [dialogoCancelarAbierto, setDialogoCancelarAbierto] = useState(false)
  const [notas, setNotas] = useState(asesoria.notas)
  const [error, setError] = useState<string | null>(null)

  if (asesoria.estado === 'cancelada') {
    return (
      <section className="rounded-lg bg-surface-container-low p-4">
        <p className="text-sm text-on-surface-variant">
          Esta asesoría fue cancelada. El motivo no está disponible todavía en
          la API (ver deuda técnica 0010) — el campo existe en el backend pero
          no se expone en el serializer.
        </p>
      </section>
    )
  }

  if (asesoria.estado === 'realizada') {
    return (
      <section className="flex flex-col gap-3 rounded-lg bg-surface-container-low p-4">
        <p className="text-sm text-on-surface">{asesoria.asistio ? 'El alumno asistió.' : 'El alumno no asistió.'}</p>
        {puedeGuardarNotas(asesoria) ? (
          <>
            <textarea
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              rows={4}
              placeholder="Notas de la sesión…"
              className="rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
            />
            <Boton
              type="button"
              disabled={notas === asesoria.notas}
              cargando={guardarNotas.isPending}
              onClick={() =>
                guardarNotas.mutate(
                  { id: asesoria.id, texto: notas },
                  {
                    onSuccess: () => {
                      setError(null)
                      mostrar('Notas guardadas')
                    },
                    onError: (err) => setError(primerMensajeDeError(err)),
                  },
                )
              }
              className="w-fit px-6"
            >
              Guardar notas
            </Boton>
            {error && <p role="alert" className="text-xs text-error">{error}</p>}
          </>
        ) : null}
        <Retroalimentacion mensaje={mensaje} />
      </section>
    )
  }

  const yaOcurrio = sesionYaOcurrio(asesoria, new Date())

  return (
    <section className="flex flex-col gap-3 rounded-lg bg-surface-container-low p-4">
      {yaOcurrio ? (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-on-surface">¿El alumno asistió a esta sesión?</p>
          <div className="flex gap-2">
            <Boton
              type="button"
              cargando={marcarAsistencia.isPending}
              onClick={() =>
                marcarAsistencia.mutate(
                  { id: asesoria.id, asistio: true },
                  {
                    onSuccess: () => {
                      setError(null)
                      mostrar('Asistencia registrada')
                    },
                    onError: (err) => setError(primerMensajeDeError(err)),
                  },
                )
              }
              className="flex-1"
            >
              Asistió
            </Boton>
            <Boton
              type="button"
              variante="secundario"
              cargando={marcarAsistencia.isPending}
              onClick={() =>
                marcarAsistencia.mutate(
                  { id: asesoria.id, asistio: false },
                  {
                    onSuccess: () => {
                      setError(null)
                      mostrar('Asistencia registrada')
                    },
                    onError: (err) => setError(primerMensajeDeError(err)),
                  },
                )
              }
              className="flex-1"
            >
              No asistió
            </Boton>
          </div>
          {error && <p role="alert" className="text-xs text-error">{error}</p>}
        </div>
      ) : (
        <p className="text-xs text-on-surface-variant">
          Podrás marcar asistencia después de las {FORMATEADOR_HORA.format(new Date(`${asesoria.fecha}T${asesoria.hora_inicio}`))}.
        </p>
      )}

      <Boton variante="peligro" type="button" onClick={() => setDialogoCancelarAbierto(true)} className="w-fit px-6">
        Cancelar asesoría
      </Boton>

      <DialogoCancelar
        abierto={dialogoCancelarAbierto}
        cargando={cancelar.isPending}
        error={error}
        onConfirmar={(motivo) =>
          cancelar.mutate(
            { id: asesoria.id, motivo },
            {
              onSuccess: () => {
                setDialogoCancelarAbierto(false)
                setError(null)
                mostrar('Asesoría cancelada')
              },
              onError: (err) => setError(primerMensajeDeError(err)),
            },
          )
        }
        onCerrar={() => setDialogoCancelarAbierto(false)}
      />
      <Retroalimentacion mensaje={mensaje} />
    </section>
  )
}
