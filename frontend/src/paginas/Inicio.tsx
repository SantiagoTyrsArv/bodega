import { useUsuarioActual } from '../api/auth'

export default function Inicio() {
  const { data: usuario } = useUsuarioActual()

  return (
    <section>
      <h1 className="text-2xl font-bold text-slate-800">Inicio</h1>
      <p className="mt-2 text-slate-600">Hola, {usuario?.nombre}.</p>
    </section>
  )
}
