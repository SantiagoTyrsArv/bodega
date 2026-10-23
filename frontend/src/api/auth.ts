import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { TokenSalida, Usuario } from '../tipos'
import { ErrorApi, guardarToken, peticion } from './cliente'

export const CLAVE_YO = ['yo']

/**
 * Usuario con sesión, o null si no hay. Al recargar la página no hay token en memoria:
 * el 401 de /auth/yo dispara la renovación con la cookie y así se recupera la sesión.
 */
export function useUsuarioActual() {
  return useQuery({
    queryKey: CLAVE_YO,
    queryFn: async () => {
      try {
        return await peticion<Usuario>('/auth/yo')
      } catch (e) {
        if (e instanceof ErrorApi && e.estado === 401) return null
        throw e
      }
    },
    staleTime: Infinity,
    // El 401 ya se convierte en null; los demás errores (sin conexión, API arrancando) se reintentan
    retry: 2,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (datos: { correo: string; clave: string }) =>
      peticion<TokenSalida>('/auth/login', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: (datos) => {
      guardarToken(datos.access_token)
      queryClient.setQueryData(CLAVE_YO, datos.usuario)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => peticion<void>('/auth/logout', { method: 'POST' }),
    onSettled: () => {
      // Aunque falle la petición, se cierra la sesión local
      guardarToken(null)
      queryClient.removeQueries()
      queryClient.setQueryData(CLAVE_YO, null)
    },
  })
}
