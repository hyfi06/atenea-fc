import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { MenuUsuario } from '../components/MenuUsuario'
import { IconTutorias } from '../components/icons/ServiceIcons'
import { useEsAcademico, useEsAlumno, useEsMiembroSAE } from '../auth/rol'

/**
 * Los tiles son los servicios que existen de verdad y que este usuario puede
 * usar, no un catálogo aspiracional (ADR 0027 decisión 9). Se arman en el
 * cliente a partir de `roles`: todavía no hay un endpoint de catálogo de
 * servicios de la SAE (deuda 0019).
 */
export function Home() {
  const navigate = useNavigate()
  const esAlumno = useEsAlumno()
  const esAcademico = useEsAcademico()
  const esMiembroSAE = useEsMiembroSAE()

  const tiles = [
    {
      id: 'asesorias',
      etiqueta: 'Asesorías',
      ruta: '/asesorias',
      visible: esAlumno || esAcademico,
      containerClassName: 'bg-primary-container text-on-primary-container',
    },
    {
      id: 'sae-asesorias',
      etiqueta: 'Asesorías · SAE',
      ruta: '/sae/asesorias',
      visible: esMiembroSAE,
      containerClassName: 'bg-secondary-container text-on-secondary-container',
    },
  ].filter((tile) => tile.visible)

  return (
    <main className="min-h-svh px-4 pb-8">
      <header className="flex items-center gap-2 py-4">
        <Logo className="h-7 w-7 text-primary" />
        <span className="text-base font-semibold">Atenea</span>
        <span className="flex-1" />
        <MenuUsuario />
      </header>

      <p className="pb-4 text-sm text-on-surface-variant">Hola</p>

      {tiles.length === 0 ? (
        <p className="text-sm text-on-surface-variant">Aún no contamos con servicios para ti.</p>
      ) : (
        <div className="grid grid-cols-3 gap-3">
          {tiles.map((tile, indice) => (
            <button
              key={tile.id}
              type="button"
              onClick={() => navigate(tile.ruta)}
              style={{ animationDelay: `${indice * 30}ms` }}
              className={`entrada-lista presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl p-3 text-center ${tile.containerClassName}`}
            >
              <IconTutorias className="h-6 w-6" />
              <span className="text-xs font-semibold leading-tight">{tile.etiqueta}</span>
            </button>
          ))}
        </div>
      )}
    </main>
  )
}