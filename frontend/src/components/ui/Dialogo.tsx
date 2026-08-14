import type { ReactNode } from 'react'

import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

type TonoAccion = 'primario' | 'peligro'

export interface AccionDialogo {
  etiqueta: string
  onClick: () => void
  /** `peligro` para acciones destructivas. Default `primario`. */
  tono?: TonoAccion
  cargando?: boolean
  deshabilitada?: boolean
}

interface DialogoProps {
  abierto: boolean
  titulo: string
  descripcion?: string
  /** Mensaje de error de la última acción, se anuncia con role="alert". */
  error?: string | null
  /**
   * Acciones ordenadas de menor a mayor consecuencia. La acción de salir NO
   * va aquí: la construye el componente, porque su posición y su estilo son
   * parte de la convención.
   */
  acciones: AccionDialogo[]
  etiquetaSalir?: string
  onCerrar: () => void
  children?: ReactNode
}

// `min-w-0` + `whitespace-normal` son el fix de overflow del paso 3: sin
// ellos un botón con flex-1 no se encoge por debajo del ancho de su propio
// texto y el par se desborda. Por eso también `min-h-11` en vez de una
// altura fija: el botón tiene que poder crecer a dos líneas.
const BASE_BOTON =
  'presionable foco-visible flex min-h-11 min-w-0 items-center justify-center gap-2 whitespace-normal rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60'

const RELLENO: Record<TonoAccion, string> = {
  primario: 'bg-primary text-on-primary',
  peligro: 'bg-error-container text-on-error-container',
}

const CONTORNO: Record<TonoAccion, string> = {
  primario: 'border border-outline bg-transparent text-primary',
  peligro: 'border border-error bg-transparent text-error',
}

const TEXTO_PLANO = 'bg-transparent text-primary'

function BotonDialogo({ accion, className }: { accion: AccionDialogo; className?: string }) {
  return (
    <button
      type="button"
      onClick={accion.onClick}
      disabled={accion.deshabilitada === true || accion.cargando === true}
      className={cn(BASE_BOTON, className)}
    >
      {accion.cargando === true && <span className="spinner h-4 w-4" aria-hidden />}
      {accion.etiqueta}
    </button>
  )
}

/**
 * Diálogo compartido de Atenea. Envuelve el primitivo `dialog` de shadcn y
 * codifica **una sola vez** la convención de orden de botones fijada en el
 * paso 3 del rediseño:
 *
 * - 2 acciones (una `accion` + salir) → fila: salir a la izquierda, la
 *   acción de confirmación a la derecha con su estilo semántico.
 * - 3+ acciones → columna a ancho completo: la reversible arriba (única que
 *   puede ir rellena), las consecuentes en contorno (nunca rellenas, para
 *   que la destructiva no se lea como la opción fácil), y salir al final
 *   como texto plano.
 *
 * Los diálogos específicos de un feature componen este componente; no
 * vuelven a montar `Dialog.Root`/`Portal`/`Overlay` por su cuenta.
 */
export function Dialogo({
  abierto,
  titulo,
  descripcion,
  error,
  acciones,
  etiquetaSalir = 'Volver',
  onCerrar,
  children,
}: DialogoProps) {
  const enColumna = acciones.length > 1
  const accionSalir: AccionDialogo = { etiqueta: etiquetaSalir, onClick: onCerrar }

  return (
    <Dialog open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <DialogContent>
        <div className="flex flex-col gap-1">
          <DialogTitle>{titulo}</DialogTitle>
          {descripcion !== undefined && <DialogDescription>{descripcion}</DialogDescription>}
        </div>

        {children}

        {error != null && error !== '' && (
          <p role="alert" className="text-xs text-error">
            {error}
          </p>
        )}

        <div className={cn('flex gap-2', enColumna ? 'flex-col' : 'flex-row')}>
          {enColumna ? (
            <>
              {acciones.map((accion, indice) => (
                <BotonDialogo
                  key={accion.etiqueta}
                  accion={accion}
                  className={indice === 0 ? RELLENO[accion.tono ?? 'primario'] : CONTORNO[accion.tono ?? 'primario']}
                />
              ))}
              <BotonDialogo accion={accionSalir} className={cn(TEXTO_PLANO, 'mt-1')} />
            </>
          ) : (
            <>
              <BotonDialogo accion={accionSalir} className={cn(CONTORNO.primario, 'flex-1')} />
              {acciones.map((accion) => (
                <BotonDialogo
                  key={accion.etiqueta}
                  accion={accion}
                  className={cn(RELLENO[accion.tono ?? 'primario'], 'flex-1')}
                />
              ))}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
