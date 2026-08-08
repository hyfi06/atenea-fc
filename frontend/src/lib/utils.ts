import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Combina clases condicionales y resuelve conflictos de Tailwind.
 *  Es la utilidad que todos los primitivos generados por shadcn importan. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
