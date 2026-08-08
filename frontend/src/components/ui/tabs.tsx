import * as React from 'react'
import * as TabsPrimitive from '@radix-ui/react-tabs'

import { cn } from '@/lib/utils'

/**
 * Primitivo `tabs` de shadcn/ui (ADR 0020), curado para este proyecto.
 *
 * El estilo por default es el subrayado que la app ya usaba en
 * `SesionesAsesor` (Próximas/Historial), no el "pill" con `bg-muted` que
 * trae shadcn: es el lenguaje visual establecido y evita introducir un
 * segundo patrón de pestañas. Cada consumidor puede afinar el layout con
 * `className` (p. ej. el espaciado de los 7 días en "Mi horario").
 *
 * La navegación con flechas, Home/End y el manejo de foco los resuelve
 * Radix; no se interceptan (checklist del paso 7).
 */

function Tabs({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return <TabsPrimitive.Root data-slot="tabs" className={cn('flex flex-col', className)} {...props} />
}

function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn('mb-4 flex gap-4 border-b border-outline-variant text-sm', className)}
      {...props}
    />
  )
}

function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        'foco-visible min-h-11 px-1 pb-2 text-on-surface-variant',
        'data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary',
        className,
      )}
      {...props}
    />
  )
}

function TabsContent({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return <TabsPrimitive.Content data-slot="tabs-content" className={cn('outline-none', className)} {...props} />
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
