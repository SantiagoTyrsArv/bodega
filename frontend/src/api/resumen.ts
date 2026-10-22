import { useQuery } from '@tanstack/react-query'
import type { Resumen } from '../tipos'
import { peticion } from './cliente'

export function useResumen() {
  return useQuery({
    queryKey: ['resumen'],
    queryFn: () => peticion<Resumen>('/resumen'),
  })
}
