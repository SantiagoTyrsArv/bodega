import { Link, Navigate, useNavigate } from 'react-router'
import { useUsuarioActual } from '../api/auth'
import { useCrearProducto } from '../api/productos'
import FormProducto from '../componentes/FormProducto'

export default function ProductoNuevo() {
  const { data: usuario } = useUsuarioActual()
  const crear = useCrearProducto()
  const navegar = useNavigate()

  if (usuario?.rol !== 'ADMIN') return <Navigate to="/productos" replace />

  return (
    <section className="mx-auto max-w-lg space-y-4">
      <Link to="/productos" className="text-sm text-slate-600 hover:underline">
        ← Productos
      </Link>
      <h1 className="text-2xl font-bold text-slate-800">Nuevo producto</h1>
      <div className="tarjeta">
        <FormProducto
          textoBoton="Crear producto"
          pendiente={crear.isPending}
          error={crear.error}
          onEnviar={(datos) =>
            crear.mutate(datos, { onSuccess: (p) => navegar(`/productos/${p.id}`, { replace: true }) })
          }
        />
      </div>
    </section>
  )
}
