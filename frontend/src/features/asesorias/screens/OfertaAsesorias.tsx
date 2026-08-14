import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOferta } from '../api'
import { useMapaCarreras } from '../../catalogo/api'
import { Skeleton } from '../../../components/ui/Skeleton'

interface OfertaAsesoriasProps {
  /** Encabezado de la pantalla. */
  titulo?: string
  /** Destino del botón de regreso. */
  rutaVolver?: string
  /** Texto del botón de regreso. */
  etiquetaVolver?: string
  /** Prefijo del destino al elegir materia: `${baseRutaMateria}/${materia_id}`. */
  baseRutaMateria?: string
}

/**
 * Listado de la oferta. El alumno lo usa como paso 1 del agendado; el SAE lo
 * reusa en modo consulta cambiando título y destinos (ADR 0024) — la pantalla
 * no agenda nada por sí misma.
 */
export function OfertaAsesorias({
  titulo = 'Nueva asesoría',
  rutaVolver = '/asesorias',
  etiquetaVolver = '← Volver a Asesorías',
  baseRutaMateria = '/asesorias/nueva',
}: OfertaAsesoriasProps) {
  const navigate = useNavigate()
  const { data: oferta = [], isPending } = useOferta()
  const mapaCarreras = useMapaCarreras()
  const [carrera, setCarrera] = useState<number | null>(null)
  const [busqueda, setBusqueda] = useState('')

  const filtradas = useMemo(
    () =>
      oferta.filter(
        (m) =>
          (carrera === null || m.carrera_id === carrera) &&
          m.nombre.toLowerCase().includes(busqueda.toLowerCase()),
      ),
    [oferta, carrera, busqueda],
  )

  const carrerasEnOferta = useMemo(() => {
    const ids = [...new Set(oferta.map((m) => m.carrera_id))]
    return ids.map((id) => ({ id, nombre: mapaCarreras.get(id)?.nombre ?? `Carrera #${id}` }))
  }, [oferta, mapaCarreras])

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={() => navigate(rutaVolver)} className="foco-visible w-fit min-h-11 text-sm text-primary">
        {etiquetaVolver}
      </button>
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>

      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="filtro-carrera" className="text-xs text-on-surface-variant">Carrera</label>
          <select
            id="filtro-carrera"
            value={carrera ?? ''}
            onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
            className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          >
            <option value="">Todas</option>
            {carrerasEnOferta.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="busqueda-oferta" className="text-xs text-on-surface-variant">Buscar materia</label>
          <input
            id="busqueda-oferta"
            type="text"
            placeholder="Escribe para filtrar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          />
        </div>
      </div>

      {isPending ? (
        <ul className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <li key={i}><Skeleton className="h-14" /></li>
          ))}
        </ul>
      ) : filtradas.length === 0 ? (
        <p className="text-sm text-on-surface-variant">
          {oferta.length === 0
            ? 'No hay materias con asesores disponibles.'
            : 'Ninguna materia coincide con tu búsqueda.'}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {filtradas.map((m, indice) => (
            <li key={m.materia_id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
              <button
                type="button"
                onClick={() => navigate(`${baseRutaMateria}/${m.materia_id}`)}
                className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
              >
                <span className="truncate text-sm font-medium text-on-surface" title={m.nombre}>{m.nombre}</span>
                <span className="ml-3 shrink-0 text-xs text-on-surface-variant">
                  {m.num_asesores} asesor{m.num_asesores === 1 ? '' : 'es'}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}
