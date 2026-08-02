import { useState } from 'react'
import type { Disponibilidad } from '../../../api/types'
import { claveSlot, mapaDisponibilidades } from '../logica'
import { Skeleton } from '../../../components/ui/Skeleton'

const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

function generarHoras(): string[] {
  const horas: string[] = []
  for (let h = 7; h <= 20; h++) {
    horas.push(`${String(h).padStart(2, '0')}:00:00`)
    horas.push(`${String(h).padStart(2, '0')}:30:00`)
  }
  return horas
}

const HORAS = generarHoras()

interface GrillaDisponibilidadProps {
  disponibilidades: Disponibilidad[]
  cargando: boolean
  onCeldaVacia: (diaSemana: number, horaInicio: string) => void
  onCeldaActiva: (disponibilidad: Disponibilidad) => void
}

export function GrillaDisponibilidad({ disponibilidades, cargando, onCeldaVacia, onCeldaActiva }: GrillaDisponibilidadProps) {
  const [pendientes] = useState<Set<string>>(new Set())
  const mapa = mapaDisponibilidades(disponibilidades)

  if (cargando) {
    return (
      <div className="grid grid-cols-8 gap-1">
        {Array.from({ length: 8 * 12 }).map((_, i) => (
          <Skeleton key={i} className="h-6" />
        ))}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[640px] grid-cols-8 gap-1 text-xs">
        <div />
        {DIAS.map((dia) => (
          <div key={dia} className="pb-1 text-center font-medium text-on-surface-variant">
            {dia}
          </div>
        ))}
        {HORAS.map((hora) => (
          <>
            <div key={`etiqueta-${hora}`} className="pr-2 text-right text-on-surface-variant">
              {hora.slice(0, 5)}
            </div>
            {DIAS.map((_, diaSemana) => {
              const clave = claveSlot(diaSemana, hora)
              const disponibilidad = mapa.get(clave)
              const estaPendiente = pendientes.has(clave)
              return (
                <button
                  key={clave}
                  type="button"
                  onClick={() => (disponibilidad ? onCeldaActiva(disponibilidad) : onCeldaVacia(diaSemana, hora))}
                  className={`h-6 rounded-sm border border-outline-variant transition-colors ${
                    disponibilidad
                      ? 'entrada-lista bg-primary-container hover:bg-primary'
                      : 'hover:bg-surface-container-high'
                  } ${estaPendiente ? 'animate-pulse opacity-60' : ''}`}
                  aria-label={
                    disponibilidad
                      ? `Bloque activo, ${DIAS[diaSemana]} ${hora.slice(0, 5)}, ${disponibilidad.formato}`
                      : `Crear bloque, ${DIAS[diaSemana]} ${hora.slice(0, 5)}`
                  }
                />
              )
            })}
          </>
        ))}
      </div>
    </div>
  )
}
