import { describe, expect, it } from 'vitest'
import { nombreProducto, rangoDeDias } from './formato'

describe('rangoDeDias', () => {
  it('va del inicio del primer día al inicio del día siguiente al último, en hora local', () => {
    const { desde, hasta } = rangoDeDias('2026-10-01', '2026-10-03')
    const inicio = new Date(desde!)
    const fin = new Date(hasta!)
    expect([inicio.getFullYear(), inicio.getMonth(), inicio.getDate(), inicio.getHours()]).toEqual([2026, 9, 1, 0])
    expect([fin.getFullYear(), fin.getMonth(), fin.getDate(), fin.getHours()]).toEqual([2026, 9, 4, 0])
  })

  it('el último día de un mes pasa al mes siguiente', () => {
    const fin = new Date(rangoDeDias('', '2026-10-31').hasta!)
    expect([fin.getMonth(), fin.getDate()]).toEqual([10, 1])
  })

  it('sin fechas no filtra', () => {
    expect(rangoDeDias('', '')).toEqual({})
    expect(rangoDeDias('2026-10-01', '')).not.toHaveProperty('hasta')
  })
})

describe('nombreProducto', () => {
  it('agrega la presentación si existe', () => {
    expect(nombreProducto({ nombre: 'Coca-Cola', presentacion: '1.5 L' })).toBe('Coca-Cola 1.5 L')
    expect(nombreProducto({ nombre: 'Arroz', presentacion: null })).toBe('Arroz')
  })
})
