import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useBuscarCodigo } from '../api/productos'
import { AvisoCodigoNuevo, IconoCamara } from '../componentes/Buscador'
import Escaner from '../componentes/Escaner'

export default function Inicio() {
  const { data: usuario } = useUsuarioActual()
  const navegar = useNavigate()
  const [escaneando, setEscaneando] = useState(false)
  const codigo = useBuscarCodigo((p) => navegar(`/productos/${p.id}`))

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Inicio</h1>
      <p className="text-slate-600">Hola, {usuario?.nombre}.</p>

      <button
        onClick={() => setEscaneando(true)}
        disabled={codigo.pendiente}
        className="boton-primario min-h-20 w-full text-xl sm:max-w-sm"
      >
        <IconoCamara className="size-8" />
        {codigo.pendiente ? 'Buscando…' : 'Escanear'}
      </button>

      {codigo.noEncontrado && <AvisoCodigoNuevo codigo={codigo.noEncontrado} />}
      {codigo.error && <p className="text-sm text-red-700">{codigo.error}</p>}

      {escaneando && (
        <Escaner
          onCerrar={() => setEscaneando(false)}
          onLeer={(c) => {
            setEscaneando(false)
            codigo.buscar(c)
          }}
        />
      )}
    </section>
  )
}
