import { useMemo, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useMaterias } from '../../catalogo/api'
import { Boton } from '../../../components/ui/Boton'

interface DialogoAgregarMateriaProps {
  abierto: boolean
  cargando: boolean
  error: string | null
  onConfirmar: (materiaId: number) => void
  onCerrar: () => void
}

export function DialogoAgregarMateria({ abierto, cargando, error, onConfirmar, onCerrar }: DialogoAgregarMateriaProps) {
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
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-4 text-sm font-semibold text-on-surface">Agregar materia</Dialog.Title>

          <input
            type="text"
            placeholder="Buscar materia…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="mb-3 h-10 w-full rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          />

          <ul className="mb-3 max-h-48 overflow-y-auto">
            {filtradas.map((materia) => (
              <li key={materia.id}>
                <button
                  type="button"
                  onClick={() => setSeleccionada(materia.id)}
                  className={`w-full rounded-md px-2 py-2 text-left text-sm ${
                    seleccionada === materia.id ? 'bg-primary-container text-on-primary-container' : 'text-on-surface hover:bg-surface-container-high'
                  }`}
                >
                  {materia.nombre}
                </button>
              </li>
            ))}
          </ul>

          {error && <p role="alert" className="mb-3 text-xs text-error">{error}</p>}

          <div className="flex gap-2">
            <Boton variante="secundario" type="button" onClick={onCerrar} className="flex-1">
              Cancelar
            </Boton>
            <Boton
              type="button"
              disabled={seleccionada === null}
              cargando={cargando}
              onClick={() => seleccionada !== null && onConfirmar(seleccionada)}
              className="flex-1"
            >
              Agregar
            </Boton>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
