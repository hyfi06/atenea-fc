import { useNavigate } from 'react-router-dom'

import { Boton } from '@/components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '@/components/ui/Retroalimentacion'
import { useCrearRegistro } from '../api'
import { semestreActual } from '../logica'
import { useRegistroAsesoresAbierto } from '../../academico/api'

/**
 * Pantalla de "todavía no tienes registro de asesor para este semestre".
 * Estado compartido por "Mis materias" y "Mi horario": sin registro no hay
 * ni materias ni horario que mostrar.
 */
export function SinRegistroAsesor({ titulo }: { titulo: string }) {
  const navigate = useNavigate()
  const crearRegistro = useCrearRegistro()
  const { mensaje, saliendo, mostrar } = useRetroalimentacion()
  const semestre = semestreActual()
  const ventanaAbierta = useRegistroAsesoresAbierto()

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>
      <p className="text-sm text-on-surface-variant">
        Aún no tienes un registro de asesor para este semestre.
      </p>

      {ventanaAbierta ? (
        <Boton
          type="button"
          cargando={crearRegistro.isPending}
          onClick={() => crearRegistro.mutate(semestre, { onSuccess: () => mostrar('Registro creado') })}
          className="w-fit px-6"
        >
          Registrar semestre {semestre}
        </Boton>
      ) : (
        <p className="text-sm text-on-surface-variant">
          El registro de asesores para {semestre} no está abierto. La SAE publica las fechas
          de cada semestre.
        </p>
      )}

      <Retroalimentacion mensaje={mensaje} saliendo={saliendo} />
    </main>
  )
}
