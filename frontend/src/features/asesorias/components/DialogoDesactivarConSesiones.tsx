import { Dialogo } from '../../../components/ui/Dialogo'

interface DialogoDesactivarConSesionesProps {
  abierto: boolean
  total: number
  cargando: boolean
  error: string | null
  onSoloNuevas: () => void
  onCancelarYDesactivar: () => void
  onCerrar: () => void
}

/**
 * Advertencia al desactivar un bloque que tiene sesiones ya agendadas
 * (paso 3). Las tres acciones y su orden los fija la convención; aquí solo
 * se declaran en el orden semántico y `Dialogo` se encarga del resto.
 */
export function DialogoDesactivarConSesiones({
  abierto,
  total,
  cargando,
  error,
  onSoloNuevas,
  onCancelarYDesactivar,
  onCerrar,
}: DialogoDesactivarConSesionesProps) {
  const descripcion =
    total === 1
      ? 'Hay 1 sesión agendada en este horario.'
      : `Hay ${total} sesiones agendadas en este horario.`

  return (
    <Dialogo
      abierto={abierto}
      titulo="Este horario tiene sesiones agendadas"
      descripcion={descripcion}
      error={error}
      onCerrar={onCerrar}
      acciones={[
        { etiqueta: 'Solo dejar de recibir nuevas', cargando, onClick: onSoloNuevas },
        {
          etiqueta: 'Cancelar esas sesiones y desactivar',
          tono: 'peligro',
          cargando,
          onClick: onCancelarYDesactivar,
        },
      ]}
    />
  )
}
