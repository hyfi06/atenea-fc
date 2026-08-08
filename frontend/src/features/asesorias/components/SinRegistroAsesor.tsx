import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Boton } from '@/components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '@/components/ui/Retroalimentacion'
import { useCrearRegistro } from '../api'
import { semestreActual } from '../logica'

/**
 * Pantalla de "todavía no tienes registro de asesor para este semestre".
 * Estado compartido por "Mis materias" y "Mi horario": sin registro no hay
 * ni materias ni horario que mostrar.
 */
export function SinRegistroAsesor({ titulo }: { titulo: string }) {
  const navigate = useNavigate()
  const crearRegistro = useCrearRegistro()
  const { mensaje, mostrar } = useRetroalimentacion()
  const [semestre, setSemestre] = useState(semestreActual())

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

      <div className="flex flex-col gap-1">
        <label htmlFor="semestre-registro" className="text-xs text-on-surface-variant">
          Semestre (AAAAN)
        </label>
        <input
          id="semestre-registro"
          type="text"
          value={semestre}
          onChange={(e) => setSemestre(e.target.value)}
          className="foco-visible h-11 w-32 rounded-md border border-outline bg-transparent px-3 text-sm text-on-surface"
        />
      </div>

      <Boton
        type="button"
        cargando={crearRegistro.isPending}
        onClick={() => crearRegistro.mutate(semestre, { onSuccess: () => mostrar('Registro creado') })}
        className="w-fit px-6"
      >
        Registrar semestre {semestre}
      </Boton>

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
