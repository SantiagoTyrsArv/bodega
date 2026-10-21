export type Rol = 'ADMIN' | 'USUARIO'

export interface Usuario {
  id: number
  nombre: string
  correo: string
  rol: Rol
  activo: boolean
  creado_en: string
}

export interface TokenSalida {
  access_token: string
  token_type: string
  usuario: Usuario
}
