import type { Disponibilidad } from '../../../api/types'
import { Dialogo } from '../../../components/ui/Dialogo'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

interface DialogoBloqueActivoProps {
  abierto: boolean
  disponibilidad: Disponibilidad | null
  cargando: boolean
  onDesactivar: () => void
  onEliminar: () => void
  onCerrar: () => void
}

export function DialogoBloqueActivo({
  abierto,
  disponibilidad,
  cargando,
  onDesactivar,
  onEliminar,
  onCerrar,
}: DialogoBloqueActivoProps) {
  if (!disponibilidad) return null

  return (
    <Dialogo
      abierto={abierto}
      titulo={`${DIAS[disponibilidad.dia_semana]} ${disponibilidad.hora_inicio.slice(0, 5)} — ${disponibilidad.formato}`}
      descripcion="¿Qué quieres hacer con este bloque?"
      onCerrar={onCerrar}
      acciones={[
        { etiqueta: 'Desactivar', cargando, onClick: onDesactivar },
        { etiqueta: 'Eliminar', tono: 'peligro', cargando, onClick: onEliminar },
      ]}
    />
  )
}
