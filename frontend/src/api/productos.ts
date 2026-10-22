import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { Producto, ProductoDatos } from '../tipos'
import { ErrorApi, peticion } from './cliente'

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
    enabled: id > 0,
  })
}

/** Busca el producto de un código escaneado o escrito. Si no existe, falla con estado 404. */
export function useResolverCodigo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (codigo: string) => peticion<Producto>(`/productos/codigo/${encodeURIComponent(codigo)}`),
    onSuccess: (producto) => queryClient.setQueryData(['producto', producto.id], producto),
  })
}

/**
 * Resuelve un código leído. Si existe llama a onEncontrado; si no, deja el código en noEncontrado.
 * error trae cualquier otro problema (sin conexión, etc.).
 */
export function useBuscarCodigo(onEncontrado: (p: Producto) => void) {
  const resolver = useResolverCodigo()
  const [noEncontrado, setNoEncontrado] = useState('')

  const buscar = (codigo: string) => {
    setNoEncontrado('')
    resolver.mutate(codigo, {
      onSuccess: onEncontrado,
      onError: (e) => {
        if (e instanceof ErrorApi && e.estado === 404) setNoEncontrado(codigo)
      },
    })
  }
  const esNoEncontrado = resolver.error instanceof ErrorApi && resolver.error.estado === 404
  return {
    buscar,
    noEncontrado,
    pendiente: resolver.isPending,
    error: resolver.error && !esNoEncontrado ? resolver.error.message : '',
  }
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
