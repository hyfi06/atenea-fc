import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { MenuUsuario } from '../components/MenuUsuario'
import { IconTutorias } from '../components/icons/ServiceIcons'
import { useEsAcademico, useEsAlumno, useEsMiembroSAE } from '../auth/rol'

interface Tile {
  id: string
  etiqueta: string
  ruta: string
  visible: boolean
  /** Navegación de página completa (fuera del router de la SPA) en vez de
   *  `navigate()`. La usa "Guía de uso": vive en `frontend/public/docs/`,
   *  un árbol estático fuera de React Router — `navigate()` la mandaría a
   *  `NoEncontrado`. */
  externo?: boolean
  containerClassName: string
}

/**
 * Los tiles son los servicios que existen de verdad y que este usuario puede
 * usar, no un catálogo aspiracional (ADR 0027 decisión 9). Se arman en el
 * cliente a partir de `roles`: todavía no hay un endpoint de catálogo de
 * servicios de la SAE (deuda 0019).
 *
 * Excepción: "Guía de uso" no es un servicio ni depende de rol — es
 * documentación pública (`frontend/public/docs/`), por eso su tile siempre
 * está visible y navega con un `<a>` normal en vez de `useNavigate()`.
 */
export function Home() {
  const navigate = useNavigate()
  const esAlumno = useEsAlumno()
  const esAcademico = useEsAcademico()
  const esMiembroSAE = useEsMiembroSAE()

  const tiles: Tile[] = [
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
    {
      id: 'guia',
      etiqueta: 'Guía de uso',
      ruta: '/docs/',
      visible: true,
      externo: true,
      containerClassName: 'bg-tertiary-container text-on-tertiary-container',
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

      <div className="grid grid-cols-3 gap-3">
        {tiles.map((tile, indice) =>
          tile.externo ? (
            <a
              key={tile.id}
              href={tile.ruta}
              style={{ animationDelay: `${indice * 30}ms` }}
              className={`entrada-lista presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl p-3 text-center ${tile.containerClassName}`}
            >
              <IconTutorias className="h-6 w-6" />
              <span className="text-xs font-semibold leading-tight">{tile.etiqueta}</span>
            </a>
          ) : (
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
          ),
        )}
      </div>
    </main>
  )
}