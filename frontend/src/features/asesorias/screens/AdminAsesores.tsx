import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAdminAsesores } from '../api'
import { Skeleton } from '../../../components/ui/Skeleton'

/**
 * Directorio de asesores para la SAE. El filtro es en cliente: el listado
 * completo ya viene en una sola petición (sin paginación, deuda 0006).
 */
export function AdminAsesores() {
  const navigate = useNavigate()
  const { data: asesores = [], isPending } = useAdminAsesores()
  const [busqueda, setBusqueda] = useState('')

  const filtrados = useMemo(
    () => asesores.filter((a) => a.nombre.toLowerCase().includes(busqueda.toLowerCase())),
    [asesores, busqueda],
  )

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/sae/asesorias')}
        className="foco-visible w-fit min-h-11 text-sm text-primary"
      >
        ← Volver a Asesorías SAE
      </button>
      <h1 className="text-lg font-semibold text-on-background">Asesores</h1>

      <div className="flex flex-col gap-1">
        <label htmlFor="busqueda-asesor" className="text-xs text-on-surface-variant">Buscar asesor</label>
        <input
          id="busqueda-asesor"
          type="text"
          placeholder="Escribe para filtrar…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
        />
      </div>

      {isPending ? (
        <ul className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <li key={i}><Skeleton className="h-16" /></li>
          ))}
        </ul>
      ) : filtrados.length === 0 ? (
        <p className="text-sm text-on-surface-variant">
          {asesores.length === 0
            ? 'No hay asesores registrados.'
            : 'Ningún asesor coincide con tu búsqueda.'}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {filtrados.map((a, indice) => (
            <li key={a.perfil_id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
              <button
                type="button"
                onClick={() => navigate(`/sae/asesores/${a.perfil_id}`)}
                className="foco-visible flex min-h-11 w-full items-center justify-between gap-3 rounded-lg bg-surface-container px-4 py-3 text-left"
              >
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="truncate text-sm font-medium text-on-surface" title={a.nombre}>{a.nombre}</span>
                  <span className="truncate text-xs text-on-surface-variant">{a.area_nombre}</span>
                </span>
                <span className="flex shrink-0 flex-col items-end gap-1">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      a.activo
                        ? 'bg-primary-container text-on-primary-container'
                        : 'bg-surface-variant text-on-surface-variant'
                    }`}
                  >
                    {a.activo ? 'Activo' : 'Inactivo'}
                  </span>
                  <span className="text-xs text-on-surface-variant">
                    {a.num_materias_semestre_vigente} materia{a.num_materias_semestre_vigente === 1 ? '' : 's'}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}
