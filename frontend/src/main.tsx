import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { CLAVE_YO } from './api/auth'
import { alExpirarSesion } from './api/cliente'
import Layout from './componentes/Layout'
import './index.css'
import Ajustes from './paginas/Ajustes'
import Inicio from './paginas/Inicio'
import Login from './paginas/Login'
import ProductoDetalle from './paginas/ProductoDetalle'
import ProductoNuevo from './paginas/ProductoNuevo'
import Productos from './paginas/Productos'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

// Si la sesión no se puede renovar, se marca sin usuario y el Layout manda al login
alExpirarSesion(() => queryClient.setQueryData(CLAVE_YO, null))

const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    element: <Layout />,
    children: [
      { index: true, element: <Inicio /> },
      { path: 'productos', element: <Productos /> },
      { path: 'productos/nuevo', element: <ProductoNuevo /> },
      { path: 'productos/:id', element: <ProductoDetalle /> },
      { path: 'ajustes', element: <Ajustes /> },
      { path: '*', element: <p className="text-slate-600">Página no encontrada.</p> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
