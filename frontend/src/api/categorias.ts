import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Categoria } from '../tipos'
import { peticion } from './cliente'

export function useCategorias() {
  return useQuery({
    queryKey: ['categorias'],
    queryFn: () => peticion<Categoria[]>('/categorias'),
  })
}

export function useGuardarCategoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, nombre }: { id?: number; nombre: string }) =>
      peticion<Categoria>(id ? `/categorias/${id}` : '/categorias', {
        method: id ? 'PATCH' : 'POST',
        body: JSON.stringify({ nombre }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categorias'] })
      // Los productos muestran el nombre de su categoría
      queryClient.invalidateQueries({ queryKey: ['productos'] })
      queryClient.invalidateQueries({ queryKey: ['producto'] })
    },
  })
}
