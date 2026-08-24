import { useEffect, useMemo, useRef, useState } from 'react'

import { Dialogo } from '../../../components/ui/Dialogo'
import { useCarreras, useMateriasInfinitas } from '../../catalogo/api'

/** Evita una request por tecla mientras el asesor escribe. */
const RETRASO_BUSQUEDA_MS = 300

interface DialogoAgregarMateriaProps {
  abierto: boolean
  cargando: boolean
  error: string | null
  onConfirmar: (materiaId: number) => void
  onCerrar: () => void
}

export function DialogoAgregarMateria({
  abierto,
  cargando,
  error,
  onConfirmar,
  onCerrar,
}: DialogoAgregarMateriaProps) {
  const [busqueda, setBusqueda] = useState('')
  const [busquedaDiferida, setBusquedaDiferida] = useState('')
  const [carrera, setCarrera] = useState<number | null>(null)
  const [seleccionada, setSeleccionada] = useState<number | null>(null)
  const sentinelaRef = useRef<HTMLLIElement | null>(null)

  useEffect(() => {
    const temporizador = setTimeout(() => setBusquedaDiferida(busqueda), RETRASO_BUSQUEDA_MS)
    return () => clearTimeout(temporizador)
  }, [busqueda])

  // Catálogo completo de carreras, no derivado de las materias cargadas: con
  // scroll infinito el selector estaría incompleto hasta scrollear todo.
  const { data: carreras = [] } = useCarreras()

  // El filtro por texto y por carrera ya no corre en cliente: viaja al backend
  // como `search` y `carrera`, y ambos entran a la queryKey del hook.
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useMateriasInfinitas({
    habilitada_asesorias: true,
    carrera,
    search: busquedaDiferida,
  })

  const materias = useMemo(() => (data?.pages ?? []).flatMap((pagina) => pagina.results), [data])

  // El sentinela es el último `<li>` del contenedor con overflow: cuando entra
  // a la vista, se pide la página siguiente. Solo se monta si `hasNextPage`.
  useEffect(() => {
    const nodo = sentinelaRef.current
    if (nodo === null || !hasNextPage) return
    const observador = new IntersectionObserver((entradas) => {
      if (entradas[0]?.isIntersecting === true) void fetchNextPage()
    })
    observador.observe(nodo)
    return () => observador.disconnect()
  }, [hasNextPage, fetchNextPage, materias.length])

  return (
    <Dialogo
      abierto={abierto}
      titulo="Agregar materia"
      error={error}
      etiquetaSalir="Cancelar"
      onCerrar={onCerrar}
      acciones={[
        {
          etiqueta: 'Agregar',
          cargando,
          deshabilitada: seleccionada === null,
          onClick: () => seleccionada !== null && onConfirmar(seleccionada),
        },
      ]}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="carrera-materia" className="text-xs text-on-surface-variant">
            Carrera
          </label>
          <select
            id="carrera-materia"
            value={carrera ?? ''}
            onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
            className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          >
            <option value="">Todas</option>
            {carreras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="busqueda-materia" className="text-xs text-on-surface-variant">
            Buscar materia
          </label>
          <input
            id="busqueda-materia"
            type="text"
            placeholder="Escribe para filtrar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="foco-visible h-10 w-full rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          />
        </div>

        <ul className="max-h-48 overflow-y-auto">
          {materias.map((materia, indice) => (
            <li key={materia.id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
              <button
                type="button"
                onClick={() => setSeleccionada(materia.id)}
                aria-pressed={seleccionada === materia.id}
                className={`foco-visible min-h-11 w-full rounded-md px-2 py-2 text-left text-sm ${
                  seleccionada === materia.id
                    ? 'bg-primary-container text-on-primary-container'
                    : 'fila-interactiva text-on-surface'
                }`}
              >
                {materia.nombre}
              </button>
            </li>
          ))}
          {hasNextPage && (
            <li ref={sentinelaRef} className="py-3 text-center text-xs text-on-surface-variant">
              {isFetchingNextPage ? 'Cargando más…' : ''}
            </li>
          )}
        </ul>
      </div>
    </Dialogo>
  )
}
