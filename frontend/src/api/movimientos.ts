import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Movimiento, MovimientoDatos, Pagina, TipoMovimiento } from '../tipos'
import { peticion } from './cliente'

export interface FiltrosMovimientos {
  desde?: string
  hasta?: string
  tipo?: TipoMovimiento
  producto_id?: number
  pagina?: number
  por_pagina?: number
}

export function useMovimientos(filtros: FiltrosMovimientos = {}) {
  const params = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== '') params.set(clave, String(valor))
  }
  return useQuery({
    queryKey: ['movimientos', filtros],
    queryFn: () => peticion<Pagina<Movimiento>>(`/movimientos?${params}`),
    placeholderData: keepPreviousData,
  })
}

/** Registrar o anular cambia stock, listas, historial y resumen: se refresca todo eso. */
function useAlCambiarInventario() {
  const queryClient = useQueryClient()
  return (m: Movimiento) => {
    queryClient.invalidateQueries({ queryKey: ['productos'] })
    queryClient.invalidateQueries({ queryKey: ['producto', m.producto.id] })
    queryClient.invalidateQueries({ queryKey: ['movimientos'] })
    queryClient.invalidateQueries({ queryKey: ['resumen'] })
  }
}

export function useRegistrarMovimiento() {
  const alCambiar = useAlCambiarInventario()
  return useMutation({
    mutationFn: (datos: MovimientoDatos) =>
      peticion<Movimiento>('/movimientos', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: alCambiar,
  })
}

export function useAnularMovimiento() {
  const alCambiar = useAlCambiarInventario()
  return useMutation({
    mutationFn: (id: number) => peticion<Movimiento>(`/movimientos/${id}/anular`, { method: 'POST' }),
    onSuccess: alCambiar,
  })
}
