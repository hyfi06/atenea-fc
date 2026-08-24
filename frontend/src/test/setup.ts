import '@testing-library/jest-dom/vitest'

// jsdom no implementa IntersectionObserver y el scroll infinito del catálogo
// de materias lo construye dentro de un efecto. Stub no-op por defecto: los
// tests que necesitan disparar la intersección lo sobreescriben en su archivo.
class ObservadorInterseccionStub {
  readonly root: Element | null = null
  readonly rootMargin: string = ''
  readonly thresholds: readonly number[] = []
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

globalThis.IntersectionObserver =
  ObservadorInterseccionStub as unknown as typeof IntersectionObserver
