import type { TokenSalida } from '../tipos'

// URL base de la API, definida en frontend/.env
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

/** Error de la API con el mensaje en español que envía el backend en "detail". */
export class ErrorApi extends Error {
  estado: number

  constructor(estado: number, mensaje: string) {
    super(mensaje)
    this.estado = estado
  }
}

// El access token vive solo en memoria; el refresh token va en una cookie httpOnly
let accessToken: string | null = null
let renovando: Promise<boolean> | null = null
let alExpirar: (() => void) | null = null

export function guardarToken(token: string | null) {
  accessToken = token
}

/** Registra qué hacer cuando la sesión expira y no se puede renovar. */
export function alExpirarSesion(fn: () => void) {
  alExpirar = fn
}

// Rutas de auth que no deben disparar una renovación automática
const SIN_RENOVAR = ['/auth/login', '/auth/refresh', '/auth/logout']

/** Pide un access token nuevo usando la cookie. Varias llamadas a la vez comparten la misma. */
function renovarToken(): Promise<boolean> {
  renovando ??= fetch(`${API_URL}/auth/refresh`, { method: 'POST', credentials: 'include' })
    .then(async (r) => {
      if (!r.ok) return false
      const datos: TokenSalida = await r.json()
      accessToken = datos.access_token
      return true
    })
    .catch(() => false)
    .finally(() => {
      renovando = null
    })
  return renovando
}

export async function peticion<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const enviar = () => {
    const headers = new Headers(opciones.headers)
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
    if (opciones.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
    return fetch(`${API_URL}${ruta}`, { ...opciones, headers, credentials: 'include' })
  }

  let respuesta: Response
  try {
    respuesta = await enviar()
    if (respuesta.status === 401 && !SIN_RENOVAR.includes(ruta)) {
      if (await renovarToken()) {
        respuesta = await enviar()
      } else {
        accessToken = null
        alExpirar?.()
      }
    }
  } catch {
    throw new ErrorApi(0, 'No se pudo conectar con el servidor')
  }

  if (!respuesta.ok) {
    const datos = await respuesta.json().catch(() => null)
    throw new ErrorApi(respuesta.status, datos?.detail ?? `Error ${respuesta.status}`)
  }
  if (respuesta.status === 204) return undefined as T
  return respuesta.json()
}
