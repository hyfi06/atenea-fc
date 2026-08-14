import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAdminAsesor, useAdminSemestres } from '../api'
import { Skeleton } from '../../../components/ui/Skeleton'
import { MisMaterias } from './MisMaterias'
import { MiHorario } from './MiHorario'

/**
 * Detalle read-only de un asesor para la SAE. Reutiliza "Mis materias" y
 * "Mi horario" en modo `soloLectura` con los datos de
 * GET /admin/asesores/{id}/ (ADR 0024), en vez de duplicar el layout.
 */
export function AdminAsesorDetalle() {
  const { asesorId } = useParams<{ asesorId: string }>()
  const perfilId = Number(asesorId)
  const navigate = useNavigate()
  const [semestre, setSemestre] = useState<string | null>(null)
  const { data: semestres = [] } = useAdminSemestres()
  const { data: detalle, isPending } = useAdminAsesor(
    Number.isInteger(perfilId) ? perfilId : null,
    semestre,
  )

  const volver = (
    <button
      type="button"
      onClick={() => navigate('/sae/asesores')}
      className="foco-visible w-fit min-h-11 text-sm text-primary"
    >
      ← Volver al directorio
    </button>
  )

  if (!Number.isInteger(perfilId)) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        {volver}
        <p className="text-sm text-on-surface-variant">Asesor inválido.</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      {volver}

      {isPending || !detalle ? (
        <Skeleton className="h-12" />
      ) : (
        <div className="entrada-lista flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-col gap-1">
            <h1 className="truncate text-lg font-semibold text-on-background" title={detalle.nombre}>
              {detalle.nombre}
            </h1>
            <span className="truncate text-xs text-on-surface-variant">{detalle.area_nombre}</span>
          </div>
          <span
            aria-label={detalle.activo ? 'Asesor activo' : 'Asesor inactivo'}
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs ${
              detalle.activo
                ? 'bg-primary-container text-on-primary-container'
                : 'bg-surface-variant text-on-surface-variant'
            }`}
          >
            {detalle.activo ? 'Activo' : 'Inactivo'}
          </span>
        </div>
      )}

      {/* Fuera del gate de `isPending`: al cambiar de semestre la query recarga
          y el `<select>` no debe desmontarse o perdería el foco (M2). */}
      <div className="flex flex-col gap-1">
        <label htmlFor="semestre-asesor" className="text-xs text-on-surface-variant">Semestre</label>
        <select
          id="semestre-asesor"
          value={semestre ?? ''}
          onChange={(e) => setSemestre(e.target.value === '' ? null : e.target.value)}
          className="foco-visible min-h-11 w-fit rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
        >
          <option value="">Semestre vigente</option>
          {semestres.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {isPending || !detalle ? (
        <Skeleton className="h-16" />
      ) : (
        <div className="entrada-lista flex flex-col gap-4">
          <MisMaterias
            soloLectura
            materias={detalle.materias}
            semestre={detalle.semestre}
          />

          <MiHorario soloLectura disponibilidades={detalle.disponibilidades} />
        </div>
      )}
    </main>
  )
}
