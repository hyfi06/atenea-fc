import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/** Debe coincidir con la duración de `.salida-menu` en `index.css`. */
const SALIDA_MENU_MS = 140

/**
 * Menú de la hamburguesa del header de Home: identidad de la sesión arriba,
 * "Cerrar sesión" abajo.
 *
 * Es un *disclosure* (aria-expanded + aria-controls), no un role="menu": en
 * un menú ARIA todo hijo tendría que ser `menuitem`, y el bloque de
 * identidad no es accionable. Tampoco usa `Dialogo`, que es modal: esto se
 * ancla al disparador y no debe apoderarse del foco de la página.
 */
export function MenuUsuario() {
  const navigate = useNavigate()
  const { user, status, logout } = useAuth()
  const [abierto, setAbierto] = useState(false)
  // `cerrando` es el guard de doble disparo del logout; `cerrandoMenu` es otra
  // cosa: la fase de salida del panel, que lo mantiene montado 140 ms para que
  // corra `.salida-menu` antes de desmontarlo.
  const [cerrando, setCerrando] = useState(false)
  const [cerrandoMenu, setCerrandoMenu] = useState(false)
  const contenedorRef = useRef<HTMLDivElement | null>(null)
  const disparadorRef = useRef<HTMLButtonElement | null>(null)
  const idPanel = useId()

  function cerrarMenu() {
    if (cerrandoMenu) return
    setCerrandoMenu(true)
    setTimeout(() => {
      setCerrandoMenu(false)
      setAbierto(false)
    }, SALIDA_MENU_MS)
  }

  useEffect(() => {
    if (!abierto) return

    function alPresionarTecla(evento: KeyboardEvent) {
      if (evento.key !== 'Escape') return
      cerrarMenu()
      // Escape devuelve el foco al disparador; un click fuera no, porque el
      // foco ya se fue a donde el usuario apuntó.
      disparadorRef.current?.focus()
    }

    // `mousedown` y no `pointerdown`: jsdom no implementa PointerEvent de
    // forma confiable, y el evento de compatibilidad cubre igual el táctil.
    function alApuntarFuera(evento: MouseEvent) {
      if (contenedorRef.current?.contains(evento.target as Node) === true) return
      cerrarMenu()
    }

    document.addEventListener('keydown', alPresionarTecla)
    document.addEventListener('mousedown', alApuntarFuera)
    return () => {
      document.removeEventListener('keydown', alPresionarTecla)
      document.removeEventListener('mousedown', alApuntarFuera)
    }
  }, [abierto, cerrandoMenu])

  async function cerrarSesion() {
    // `logout()` traga el error del POST y limpia el lado del cliente pase lo
    // que pase, así que no hay rama de error que mostrar; `cerrando` sólo
    // evita el doble disparo.
    setCerrando(true)
    await logout()
    navigate('/', { replace: true })
  }

  // /home es ruta pública: sin sesión no hay identidad que mostrar ni sesión
  // que cerrar, y un control que no hace nada es justo el bug que se arregla.
  if (status !== 'authenticated' || user === null) return null

  return (
    <div ref={contenedorRef} className="relative">
      <button
        ref={disparadorRef}
        type="button"
        aria-label="Menú"
        aria-haspopup="true"
        aria-expanded={abierto}
        aria-controls={idPanel}
        onClick={() => (abierto ? cerrarMenu() : setAbierto(true))}
        className="foco-visible flex h-11 w-11 items-center justify-center rounded-full text-on-background"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="h-5 w-5" aria-hidden>
          <line x1="4" y1="7" x2="20" y2="7" />
          <line x1="4" y1="12" x2="20" y2="12" />
          <line x1="4" y1="17" x2="20" y2="17" />
        </svg>
      </button>

      {abierto && (
        <div
          id={idPanel}
          className={`${cerrandoMenu ? 'salida-menu' : 'entrada-menu'} absolute right-0 top-12 z-10 flex w-60 flex-col gap-1 rounded-2xl bg-surface-container p-3 text-left shadow-lg`}
        >
          <span className="truncate text-sm font-medium text-on-surface" title={user.nombre_completo}>
            {user.nombre_completo}
          </span>
          <span className="truncate text-xs text-on-surface-variant" title={user.email}>
            {user.email}
          </span>
          <hr className="my-1 border-outline-variant" />
          <button
            type="button"
            onClick={cerrarSesion}
            disabled={cerrando}
            className="foco-visible flex min-h-11 items-center rounded-lg px-2 text-sm font-medium text-error disabled:opacity-60"
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  )
}
