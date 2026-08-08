import { useState } from 'react'

import { Dialogo } from '../../../components/ui/Dialogo'

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
    <Dialogo
      abierto={abierto}
      titulo="Cancelar asesoría"
      descripcion="Se notificará al alumno por correo. Esta acción no se puede deshacer."
      error={error}
      onCerrar={onCerrar}
      acciones={[
        {
          etiqueta: 'Confirmar cancelación',
          tono: 'peligro',
          cargando,
          onClick: () => onConfirmar(motivo),
        },
      ]}
    >
      <div className="flex flex-col gap-1">
        <label htmlFor="motivo-cancelacion" className="text-xs text-on-surface-variant">
          Motivo (opcional)
        </label>
        <textarea
          id="motivo-cancelacion"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          rows={3}
          className="foco-visible rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
        />
      </div>
    </Dialogo>
  )
}
