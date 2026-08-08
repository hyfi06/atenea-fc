import { Dialogo } from '../../../components/ui/Dialogo'

interface DialogoQuitarMateriaProps {
  abierto: boolean
  nombreMateria: string
  cargando: boolean
  error: string | null
  onConfirmar: () => void
  onCerrar: () => void
}

export function DialogoQuitarMateria({
  abierto,
  nombreMateria,
  cargando,
  error,
  onConfirmar,
  onCerrar,
}: DialogoQuitarMateriaProps) {
  return (
    <Dialogo
      abierto={abierto}
      titulo={`Quitar ${nombreMateria}`}
      descripcion="Ya no aparecerás como asesor de esta materia en búsquedas de alumnos. Las asesorías ya agendadas no se cancelan."
      error={error}
      etiquetaSalir="Cancelar"
      onCerrar={onCerrar}
      acciones={[{ etiqueta: 'Quitar', tono: 'peligro', cargando, onClick: onConfirmar }]}
    />
  )
}
