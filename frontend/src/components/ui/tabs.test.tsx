import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs'

function montar() {
  render(
    <Tabs defaultValue="lun">
      <TabsList>
        <TabsTrigger value="lun">Lun</TabsTrigger>
        <TabsTrigger value="mar">Mar</TabsTrigger>
      </TabsList>
      <TabsContent value="lun">Contenido de lunes</TabsContent>
      <TabsContent value="mar">Contenido de martes</TabsContent>
    </Tabs>,
  )
}

describe('tabs', () => {
  it('muestra el contenido de la pestaña por default', () => {
    montar()

    expect(screen.getByText('Contenido de lunes')).toBeInTheDocument()
    expect(screen.queryByText('Contenido de martes')).not.toBeInTheDocument()
  })

  it('cambia de panel al seleccionar otra pestaña', () => {
    montar()

    const tab = screen.getByRole('tab', { name: 'Mar' })
    tab.focus()
    fireEvent.keyDown(tab, { key: 'Enter', code: 'Enter' })
    fireEvent.click(tab)

    expect(screen.getByText('Contenido de martes')).toBeInTheDocument()
    expect(screen.queryByText('Contenido de lunes')).not.toBeInTheDocument()
  })

  it('cada pestaña lleva el estado de foco visible del paso 7', () => {
    montar()

    for (const tab of screen.getAllByRole('tab')) {
      expect(tab).toHaveClass('foco-visible')
    }
  })
})
