import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import type { FormatoAsesoria } from '../../../api/types'
import { Boton } from '../../../components/ui/Boton'

interface DialogoNuevoBloqueProps {
  abierto: boolean
  diaSemana: number | null
  horaInicio: string | null
  nombreDia: string
  cargando: boolean
  error: string | null
  onConfirmar: (datos: { formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }) => void
  onCerrar: () => void
}

export function DialogoNuevoBloque({ abierto, diaSemana, horaInicio, nombreDia, cargando, error, onConfirmar, onCerrar }: DialogoNuevoBloqueProps) {
  const [formato, setFormato] = useState<FormatoAsesoria>('virtual')
  const [ubicacion, setUbicacion] = useState('')
  const [ligaVirtual, setLigaVirtual] = useState('')

  if (diaSemana === null || horaInicio === null) return null

  return (
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-1 text-sm font-semibold text-on-surface">
            Nuevo bloque — {nombreDia} {horaInicio.slice(0, 5)}
          </Dialog.Title>
          <Dialog.Description className="mb-4 text-xs text-on-surface-variant">
            Bloque recurrente de 30 minutos cada semana.
          </Dialog.Description>

          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
              Formato
              <select
                value={formato}
                onChange={(e) => setFormato(e.target.value as FormatoAsesoria)}
                className="h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
              >
                <option value="virtual">Virtual</option>
                <option value="presencial">Presencial</option>
              </select>
            </label>

            {formato === 'virtual' ? (
              <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
                Liga de la sesión
                <input
                  type="url"
                  value={ligaVirtual}
                  onChange={(e) => setLigaVirtual(e.target.value)}
                  required
                  className="h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
                />
              </label>
            ) : (
              <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
                Ubicación
                <input
                  type="text"
                  value={ubicacion}
                  onChange={(e) => setUbicacion(e.target.value)}
                  required
                  className="h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
                />
              </label>
            )}

            {error && <p role="alert" className="text-xs text-error">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Boton variante="secundario" type="button" onClick={onCerrar} className="flex-1">
                Cancelar
              </Boton>
              <Boton
                type="button"
                cargando={cargando}
                onClick={() => onConfirmar({ formato, ubicacion, liga_virtual: ligaVirtual })}
                className="flex-1"
              >
                Crear
              </Boton>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
