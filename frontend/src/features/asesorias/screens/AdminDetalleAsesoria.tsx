import { useLocation, useNavigate } from 'react-router-dom'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import type { AsesoriaAdmin } from '../../../api/types'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
})

/** Lo que `TarjetaAsesoria` deja en el router state al navegar en modo admin. */
interface EstadoDetalleSAE {
  asesoria?: AsesoriaAdmin
  nombreMateria?: string
}

/**
 * Detalle read-only de una sesión para el área SAE.
 *
 * No hay endpoint de detalle admin y el listado está cacheado por combinación
 * de filtros (una sesión del historial no vive en la query por defecto), así
 * que la sesión llega por router state desde la tarjeta: esta pantalla no
 * consulta nada.
 *
 * Espejo de `DetalleAsesoria` sin ninguna mutación: el área /sae/* es de sólo
 * lectura, así que aquí no se monta guardar notas, cancelar ni asistencia.
 */
export function AdminDetalleAsesoria() {
  const navigate = useNavigate()
  const { state } = useLocation() as { state: EstadoDetalleSAE | null }
  const asesoria = state?.asesoria

  const volver = (
    <button
      type="button"
      onClick={() => navigate('/sae/asesorias')}
      className="foco-visible min-h-11 w-fit text-sm text-primary"
    >
      ← Volver a Asesorías SAE
    </button>
  )

  // Sin state no hay de dónde reconstruir la sesión: pasa en deep-link o al
  // recargar. En el MVP se acepta y se devuelve al usuario a la lista.
  if (!asesoria) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <p className="text-sm text-on-surface-variant">
          No se encontró la asesoría. Vuelve a la lista y ábrela desde ahí.
        </p>
        {volver}
      </main>
    )
  }

  const nombreMateria = state?.nombreMateria ?? `Materia #${asesoria.materia}`
  const notas = asesoria.notas.trim()

  return (
    <main className="flex min-h-svh flex-col gap-6 px-6 py-6">
      {volver}

      <section className="rounded-lg bg-surface-container p-4">
        <div className="mb-2 flex items-center justify-between gap-3">
          <h1 className="truncate text-base font-semibold text-on-surface" title={nombreMateria}>
            {nombreMateria}
          </h1>
          <InsigniaEstado estado={asesoria.estado} />
        </div>
        <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
          <dt>Fecha</dt>
          <dd>{FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))}</dd>
          <dt>Hora</dt>
          <dd>{asesoria.hora_inicio.slice(0, 5)}</dd>
          <dt>Alumno</dt>
          <dd>{asesoria.alumno_nombre}</dd>
          <dt>Asesor</dt>
          <dd>{asesoria.asesor_nombre}</dd>
          <dt>Formato</dt>
          <dd>
            {asesoria.formato === 'virtual' ? (
              <a
                href={asesoria.liga_virtual}
                target="_blank"
                rel="noreferrer"
                className="foco-visible text-primary underline"
              >
                Liga de la sesión
              </a>
            ) : (
              asesoria.ubicacion
            )}
          </dd>
          <dt>Asistencia</dt>
          <dd>
            {asesoria.asistio === null
              ? 'Sin registrar'
              : asesoria.asistio
                ? 'El alumno asistió'
                : 'El alumno no asistió'}
          </dd>
        </dl>
      </section>

      {notas !== '' && (
        <section className="rounded-lg bg-surface-container-low p-4">
          <h2 className="mb-2 text-sm font-medium text-on-surface">Notas de la sesión</h2>
          <p className="whitespace-pre-line text-sm text-on-surface-variant">{notas}</p>
        </section>
      )}
    </main>
  )
}
