import type { Motivo, TipoMovimiento } from './tipos'

// Igual que el backend; ANULACION no se elige a mano
export const MOTIVOS: Record<TipoMovimiento, { valor: Motivo; texto: string }[]> = {
  ENTRADA: [
    { valor: 'COMPRA', texto: 'Compra' },
    { valor: 'DEVOLUCION', texto: 'Devolución' },
    { valor: 'AJUSTE', texto: 'Ajuste' },
  ],
  SALIDA: [
    { valor: 'USO', texto: 'Uso' },
    { valor: 'VENTA', texto: 'Venta' },
    { valor: 'PERDIDA', texto: 'Pérdida' },
    { valor: 'AJUSTE', texto: 'Ajuste' },
  ],
}

export const TEXTO_MOTIVO: Record<Motivo, string> = {
  COMPRA: 'Compra',
  DEVOLUCION: 'Devolución',
  USO: 'Uso',
  VENTA: 'Venta',
  PERDIDA: 'Pérdida',
  AJUSTE: 'Ajuste',
  ANULACION: 'Anulación',
}

/**
 * Stock que quedaría tras el movimiento, solo para mostrarlo antes de confirmar
 * (el backend hace el cálculo real). Se calcula en milésimas enteras para evitar
 * errores de coma flotante. Devuelve null si la cantidad no es un número positivo.
 */
export function stockResultante(stock: string, tipo: TipoMovimiento, cantidad: string): number | null {
  const texto = cantidad.trim().replace(',', '.')
  if (!/^\d+(\.\d{1,3})?$/.test(texto) || Number(texto) <= 0) return null
  const milesimas = (v: string) => Math.round(Number(v) * 1000)
  const signo = tipo === 'ENTRADA' ? 1 : -1
  return (milesimas(stock) + signo * milesimas(texto)) / 1000
}
