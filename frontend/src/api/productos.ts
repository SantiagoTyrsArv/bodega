import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Producto, ProductoDatos } from '../tipos'
import { peticion } from './cliente'

export interface FiltrosProductos {
  q?: string
  categoria_id?: number
  bajo_minimo?: boolean
  activo?: boolean
}

export function useProductos(filtros: FiltrosProductos = {}) {
  const params = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== '') params.set(clave, String(valor))
  }
  return useQuery({
    queryKey: ['productos', filtros],
    queryFn: () => peticion<Producto[]>(`/productos?${params}`),
    // Mientras se escribe en el buscador se mantiene la lista anterior en pantalla
    placeholderData: keepPreviousData,
  })
}

export function useProducto(id: number) {
  return useQuery({
    queryKey: ['producto', id],
    queryFn: () => peticion<Producto>(`/productos/${id}`),
  })
}

function useAlGuardar() {
  const queryClient = useQueryClient()
  return (producto: Producto) => {
    queryClient.setQueryData(['producto', producto.id], producto)
    queryClient.invalidateQueries({ queryKey: ['productos'] })
  }
}

export function useCrearProducto() {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (datos: ProductoDatos) =>
      peticion<Producto>('/productos', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: alGuardar,
  })
}

export function useEditarProducto(id: number) {
  const alGuardar = useAlGuardar()
  return useMutation({
    mutationFn: (cambios: Partial<ProductoDatos> & { activo?: boolean }) =>
      peticion<Producto>(`/productos/${id}`, { method: 'PATCH', body: JSON.stringify(cambios) }),
    onSuccess: alGuardar,
  })
}
