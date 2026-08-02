import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { Boton } from '../../../components/ui/Boton'

interface DialogoCancelarProps {
  abierto: boolean
  cargando: boolean
  error: string | null
  onConfirmar: (motivo: string) => void
  onCerrar: () => void
}

export function DialogoCancelar({ abierto, cargando, error, onConfirmar, onCerrar }: DialogoCancelarProps) {
  const [motivo, setMotivo] = useState('')

  return (
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-1 text-sm font-semibold text-on-surface">Cancelar asesoría</Dialog.Title>
          <Dialog.Description className="mb-4 text-xs text-on-surface-variant">
            Se notificará al alumno por correo. Esta acción no se puede deshacer.
          </Dialog.Description>

          <label className="mb-4 flex flex-col gap-1 text-xs text-on-surface-variant">
            Motivo (opcional)
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={3}
              className="rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
            />
          </label>

          {error && <p role="alert" className="mb-3 text-xs text-error">{error}</p>}

          <div className="flex gap-2">
            <Boton variante="secundario" type="button" onClick={onCerrar} className="flex-1">
              Volver
            </Boton>
            <Boton variante="peligro" type="button" cargando={cargando} onClick={() => onConfirmar(motivo)} className="flex-1">
              Confirmar cancelación
            </Boton>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
