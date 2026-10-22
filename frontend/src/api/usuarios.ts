import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Rol, Usuario } from '../tipos'
import { CLAVE_YO } from './auth'
import { peticion } from './cliente'

export interface UsuarioDatos {
  nombre?: string
  correo?: string
  clave?: string
  rol?: Rol
  activo?: boolean
}

export function useUsuarios() {
  return useQuery({
    queryKey: ['usuarios'],
    queryFn: () => peticion<Usuario[]>('/usuarios'),
  })
}

/** Crea (sin id) o edita (con id) un usuario. */
export function useGuardarUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...datos }: UsuarioDatos & { id?: number }) =>
      peticion<Usuario>(id ? `/usuarios/${id}` : '/usuarios', {
        method: id ? 'PATCH' : 'POST',
        body: JSON.stringify(datos),
      }),
    onSuccess: (usuario) => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      // Si se editó a sí mismo, el encabezado muestra el nombre nuevo
      const yo = queryClient.getQueryData<Usuario | null>(CLAVE_YO)
      if (yo?.id === usuario.id) queryClient.setQueryData(CLAVE_YO, usuario)
    },
  })
}
