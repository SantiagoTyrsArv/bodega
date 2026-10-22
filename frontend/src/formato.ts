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

/**
 * Convierte días 'AAAA-MM-DD' (en la hora local) al rango que espera la API:
 * desde = inicio del primer día; hasta = inicio del día siguiente al último (exclusivo).
 */
export function rangoDeDias(desde: string, hasta: string): { desde?: string; hasta?: string } {
  const rango: { desde?: string; hasta?: string } = {}
  if (desde) rango.desde = new Date(`${desde}T00:00:00`).toISOString()
  if (hasta) {
    const fin = new Date(`${hasta}T00:00:00`)
    fin.setDate(fin.getDate() + 1)
    rango.hasta = fin.toISOString()
  }
  return rango
}

/** Minutos respecto a UTC de este navegador (Colombia: -300), para las fechas del Excel. */
export const desfaseLocal = () => -new Date().getTimezoneOffset()
