import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'

import { cn } from '@/lib/utils'

/**
 * Primitivo `dialog` de shadcn/ui (ADR 0020), curado para este proyecto:
 *
 * - Sin el botón "X" de cierre que trae el original: venía con un ícono de
 *   `lucide-react`, y ADR 0014 decidió íconos a mano sin librería. Además
 *   sería redundante — `Dialogo.tsx` siempre renderiza una acción de salir
 *   explícita, según la convención de botones del paso 3.
 * - Sin `tw-animate-css`: la animación de entrada usa las clases
 *   `.entrada-dialogo`/`.entrada-velo` de `index.css`, que sí están
 *   registradas en el bloque de `prefers-reduced-motion` (paso 7).
 * - Los colores usan el vocabulario de shadcn (`bg-popover`, `border`,
 *   `text-muted-foreground`), que el bloque de alias de `index.css` mapea a
 *   los roles M3 de ADR 0014.
 *
 * Las features no importan este archivo: componen `Dialogo.tsx`.
 */

function Dialog({ ...props }: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />
}

function DialogPortal({ ...props }: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />
}

function DialogClose({ ...props }: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

function DialogOverlay({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      data-slot="dialog-overlay"
      className={cn('entrada-velo fixed inset-0 z-50 bg-scrim/50', className)}
      {...props}
    />
  )
}

function DialogContent({ className, children, ...props }: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          'entrada-dialogo fixed left-1/2 top-1/2 z-50 flex max-h-[calc(100svh-2rem)] w-[calc(100%-2rem)] max-w-sm',
          '-translate-x-1/2 -translate-y-1/2 flex-col gap-4 overflow-y-auto rounded-lg border border-border',
          'bg-popover p-5 text-popover-foreground shadow-lg',
          className,
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPortal>
  )
}

function DialogTitle({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn('text-sm font-semibold text-foreground', className)}
      {...props}
    />
  )
}

function DialogDescription({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn('text-xs text-muted-foreground', className)}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogPortal,
  DialogClose,
  DialogOverlay,
  DialogContent,
  DialogTitle,
  DialogDescription,
}
