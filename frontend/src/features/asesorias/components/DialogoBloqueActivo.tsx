import * as Dialog from '@radix-ui/react-dialog'
import type { Disponibilidad } from '../../../api/types'
import { Boton } from '../../../components/ui/Boton'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

interface DialogoBloqueActivoProps {
  abierto: boolean
  disponibilidad: Disponibilidad | null
  cargando: boolean
  onDesactivar: () => void
  onEliminar: () => void
  onCerrar: () => void
}

export function DialogoBloqueActivo({ abierto, disponibilidad, cargando, onDesactivar, onEliminar, onCerrar }: DialogoBloqueActivoProps) {
  if (!disponibilidad) return null

  return (
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-1 text-sm font-semibold text-on-surface">
            {DIAS[disponibilidad.dia_semana]} {disponibilidad.hora_inicio.slice(0, 5)} — {disponibilidad.formato}
          </Dialog.Title>
          <Dialog.Description className="mb-4 text-xs text-on-surface-variant">
            ¿Qué quieres hacer con este bloque?
          </Dialog.Description>

          <div className="flex flex-col gap-2">
            <Boton variante="secundario" type="button" cargando={cargando} onClick={onDesactivar}>
              Desactivar
            </Boton>
            <Boton variante="peligro" type="button" cargando={cargando} onClick={onEliminar}>
              Eliminar
            </Boton>
            <button type="button" onClick={onCerrar} className="mt-1 text-sm text-primary">
              Cerrar
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
