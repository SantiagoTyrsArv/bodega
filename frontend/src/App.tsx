import { useEffect, useState } from 'react'
import { API_URL } from './api/cliente'

type Estado = 'cargando' | 'ok' | 'error'

export default function App() {
  const [estado, setEstado] = useState<Estado>('cargando')

  // Verificación temporal de conexión con el backend (paso 1 del MVP)
  useEffect(() => {
    fetch(`${API_URL}/salud`)
      .then((r) => setEstado(r.ok ? 'ok' : 'error'))
      .catch(() => setEstado('error'))
  }, [])

  const textos: Record<Estado, string> = {
    cargando: 'Conectando con la API…',
    ok: 'API conectada',
    error: 'No se pudo conectar con la API',
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 p-4">
      <h1 className="text-4xl font-bold text-slate-800">BODEGA</h1>
      <p
        className={
          estado === 'ok'
            ? 'text-green-700'
            : estado === 'error'
              ? 'text-red-700'
              : 'text-slate-500'
        }
      >
        {textos[estado]}
      </p>
    </main>
  )
}
