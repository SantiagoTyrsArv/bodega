import { afterEach, describe, expect, it, vi } from 'vitest'
import { ErrorApi, alExpirarSesion, guardarToken, peticion } from './cliente'

function respuesta(estado: number, cuerpo?: unknown) {
  return new Response(cuerpo === undefined ? null : JSON.stringify(cuerpo), { status: estado })
}

afterEach(() => {
  vi.unstubAllGlobals()
  guardarToken(null)
})

describe('peticion', () => {
  it('ante un 401 renueva el token con la cookie y reintenta', async () => {
    guardarToken('viejo')
    const fetchFalso = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) return respuesta(200, { access_token: 'nuevo' })
      const auth = new Headers(init?.headers).get('Authorization')
      return auth === 'Bearer nuevo' ? respuesta(200, { ok: true }) : respuesta(401)
    })
    vi.stubGlobal('fetch', fetchFalso)

    await expect(peticion('/productos')).resolves.toEqual({ ok: true })
    expect(fetchFalso).toHaveBeenCalledTimes(3)
  })

  it('varias peticiones con 401 a la vez comparten una sola renovación', async () => {
    const fetchFalso = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) return respuesta(200, { access_token: 'nuevo' })
      const auth = new Headers(init?.headers).get('Authorization')
      return auth === 'Bearer nuevo' ? respuesta(200, {}) : respuesta(401)
    })
    vi.stubGlobal('fetch', fetchFalso)

    await Promise.all([peticion('/a'), peticion('/b'), peticion('/c')])
    const renovaciones = fetchFalso.mock.calls.filter(([url]) => url.endsWith('/auth/refresh'))
    expect(renovaciones).toHaveLength(1)
  })

  it('si no se puede renovar avisa que la sesión expiró', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respuesta(401, { detail: 'No autenticado' })))
    const expiro = vi.fn()
    alExpirarSesion(expiro)

    await expect(peticion('/auth/yo')).rejects.toMatchObject({ estado: 401 })
    expect(expiro).toHaveBeenCalledOnce()
  })

  it('entrega el mensaje en español del backend', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respuesta(409, { detail: 'Stock insuficiente' })))
    const promesa = peticion('/movimientos', { method: 'POST', body: '{}' })
    await expect(promesa).rejects.toBeInstanceOf(ErrorApi)
    await expect(promesa).rejects.toThrow('Stock insuficiente')
  })
})
