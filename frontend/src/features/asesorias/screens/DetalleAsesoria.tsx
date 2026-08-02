import { useParams, useNavigate } from 'react-router-dom'
import { useMisAsesorias } from '../api'
import { useMapaMaterias, useMapaCarreras } from '../../catalogo/api'
import { sesionesPreviasConNotas } from '../logica'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { Skeleton } from '../../../components/ui/Skeleton'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

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

      {/* Sección de acciones (cancelar / marcar asistencia / notas) — Task 13 */}

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
