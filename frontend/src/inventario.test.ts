import { describe, expect, it } from 'vitest'
import { MOTIVOS, stockResultante } from './inventario'

describe('stockResultante', () => {
  it('suma en entradas y resta en salidas', () => {
    expect(stockResultante('10', 'ENTRADA', '2.5')).toBe(12.5)
    expect(stockResultante('10', 'SALIDA', '2.5')).toBe(7.5)
  })

  it('acepta coma decimal', () => {
    expect(stockResultante('1', 'ENTRADA', '0,25')).toBe(1.25)
  })

  it('no acumula errores de coma flotante', () => {
    expect(stockResultante('0.3', 'SALIDA', '0.1')).toBe(0.2)
  })

  it('devuelve null si la cantidad no es válida', () => {
    expect(stockResultante('10', 'SALIDA', '')).toBeNull()
    expect(stockResultante('10', 'SALIDA', 'abc')).toBeNull()
    expect(stockResultante('10', 'SALIDA', '0')).toBeNull()
  })
})

describe('MOTIVOS', () => {
  it('ofrece los motivos de cada tipo, sin ANULACION', () => {
    expect(MOTIVOS.ENTRADA.map((m) => m.valor)).toEqual(['COMPRA', 'DEVOLUCION', 'AJUSTE'])
    expect(MOTIVOS.SALIDA.map((m) => m.valor)).toEqual(['USO', 'VENTA', 'PERDIDA', 'AJUSTE'])
  })
})
