import { useMemo, useState } from 'react'

import { Dialogo } from '../../../components/ui/Dialogo'
import { useMaterias } from '../../catalogo/api'

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
  const { data: materias = [] } = useMaterias()
  const [busqueda, setBusqueda] = useState('')
  const [seleccionada, setSeleccionada] = useState<number | null>(null)

  const filtradas = useMemo(
    () =>
      materias.filter(
        (m) => m.habilitada_asesorias && m.nombre.toLowerCase().includes(busqueda.toLowerCase()),
      ),
    [materias, busqueda],
  )

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
          {filtradas.map((materia, indice) => (
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
        </ul>
      </div>
    </Dialogo>
  )
}
