import type { Producto, Unidad } from './tipos'

const cantidad = new Intl.NumberFormat('es', { maximumFractionDigits: 3, useGrouping: 'always' })
const dinero = new Intl.NumberFormat('es', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  useGrouping: 'always', // 'es' por defecto no agrupa números de 4 cifras (2500)
})

// Number() solo para mostrar; los cálculos de dinero los hace el backend con Decimal
export const formatoCantidad = (valor: string | number) => cantidad.format(Number(valor))
export const formatoDinero = (valor: string | number) => `$ ${dinero.format(Number(valor))}`

export const UNIDADES: Record<Unidad, string> = {
  UNIDAD: 'Unidad',
  KG: 'Kilogramo',
  LITRO: 'Litro',
  CAJA: 'Caja',
}

export const UNIDADES_CORTAS: Record<Unidad, string> = {
  UNIDAD: 'un',
  KG: 'kg',
  LITRO: 'L',
  CAJA: 'cajas',
}

/** Mismo criterio que el backend: tiene mínimo definido y el stock llegó a él. */
export const estaBajoMinimo = (p: Producto) =>
  Number(p.stock_minimo) > 0 && Number(p.stock) <= Number(p.stock_minimo)

const fecha = new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' })
export const formatoFecha = (iso: string) => fecha.format(new Date(iso))
