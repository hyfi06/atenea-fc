import { useState } from 'react'

import type { FormatoAsesoria } from '../../../api/types'
import { Dialogo } from '../../../components/ui/Dialogo'

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

const CLASE_CAMPO =
  'foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface'

export function DialogoNuevoBloque({
  abierto,
  diaSemana,
  horaInicio,
  nombreDia,
  cargando,
  error,
  onConfirmar,
  onCerrar,
}: DialogoNuevoBloqueProps) {
  const [formato, setFormato] = useState<FormatoAsesoria>('virtual')
  const [ubicacion, setUbicacion] = useState('')
  const [ligaVirtual, setLigaVirtual] = useState('')

  if (diaSemana === null || horaInicio === null) return null

  return (
    <Dialogo
      abierto={abierto}
      titulo={`Nuevo bloque — ${nombreDia} ${horaInicio.slice(0, 5)}`}
      descripcion="Bloque recurrente de 30 minutos cada semana."
      error={error}
      etiquetaSalir="Cancelar"
      onCerrar={onCerrar}
      acciones={[
        {
          etiqueta: 'Crear',
          cargando,
          onClick: () => onConfirmar({ formato, ubicacion, liga_virtual: ligaVirtual }),
        },
      ]}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="formato-bloque" className="text-xs text-on-surface-variant">
            Formato
          </label>
          <select
            id="formato-bloque"
            value={formato}
            onChange={(e) => setFormato(e.target.value as FormatoAsesoria)}
            className={CLASE_CAMPO}
          >
            <option value="virtual">Virtual</option>
            <option value="presencial">Presencial</option>
          </select>
        </div>

        {formato === 'virtual' ? (
          <div className="flex flex-col gap-1">
            <label htmlFor="liga-bloque" className="text-xs text-on-surface-variant">
              Liga de la sesión
            </label>
            <input
              id="liga-bloque"
              type="url"
              value={ligaVirtual}
              onChange={(e) => setLigaVirtual(e.target.value)}
              required
              className={CLASE_CAMPO}
            />
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            <label htmlFor="ubicacion-bloque" className="text-xs text-on-surface-variant">
              Ubicación
            </label>
            <input
              id="ubicacion-bloque"
              type="text"
              value={ubicacion}
              onChange={(e) => setUbicacion(e.target.value)}
              required
              className={CLASE_CAMPO}
            />
          </div>
        )}
      </div>
    </Dialogo>
  )
}
