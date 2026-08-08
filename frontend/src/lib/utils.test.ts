import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

describe('cn', () => {
  it('resuelve conflictos de clases de Tailwind conservando la última', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4')
  })

  it('descarta los valores condicionales falsos', () => {
    expect(cn('rounded-full', false && 'hidden', undefined, null)).toBe('rounded-full')
  })
})
