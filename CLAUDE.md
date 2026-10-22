# BODEGA

Aplicación web simple para controlar los productos de **una sola bodega**: qué hay, cuánto queda, cuánto vale y qué entra y sale. La usan de 1 a 10 personas desde celular, tablet o computador.

**Principio rector: mantenerlo simple.** No agregues funciones, librerías ni capas que no estén en este documento. Si algo parece necesario y no está aquí, pregunta antes.

Idioma: la interfaz, los mensajes de error y los nombres del dominio (tablas, campos, rutas) van en **español**. Comentarios de código en español.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite + TypeScript, Tailwind CSS, React Router, TanStack Query, React Hook Form + Zod |
| PWA | `vite-plugin-pwa` (solo para que se pueda instalar; sin modo sin conexión) |
| Escáner | `@zxing/browser` (cámara). Lectores USB/Bluetooth funcionan como teclado |
| Backend | Python 3.12 + FastAPI, SQLAlchemy 2 (estilo tipado), Alembic, Pydantic v2 |
| Auth | JWT (access 15 min + refresh en cookie httpOnly), contraseñas con Argon2 (`argon2-cffi`) |
| Excel | `openpyxl` en el backend |
| Base de datos | PostgreSQL 16 (Neon en producción, Docker en local) |
| Despliegue | Frontend en Vercel, API en Render, BD en Neon |
| Pruebas | `pytest` + `httpx` en backend; Vitest en frontend |
| Gestor de paquetes | `uv` para Python, `npm` para el frontend |

## Estructura del repositorio

```
bodega/
├── CLAUDE.md
├── docker-compose.yml        # PostgreSQL local
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py           # crea la app FastAPI, CORS, routers
│   │   ├── config.py         # Settings con pydantic-settings (lee .env)
│   │   ├── db.py             # engine, SessionLocal, get_db
│   │   ├── seguridad.py      # hash de contraseñas, JWT, dependencias de rol
│   │   ├── modelos.py        # modelos SQLAlchemy
│   │   ├── esquemas.py       # esquemas Pydantic
│   │   ├── routers/          # auth, usuarios, categorias, productos, movimientos, reportes
│   │   └── servicios/
│   │       └── inventario.py # ÚNICO lugar que cambia el stock
│   └── tests/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── api/              # cliente fetch + hooks de TanStack Query
        ├── paginas/          # Inicio, Productos, ProductoDetalle, ProductoNuevo, Movimiento, Historial, Ajustes, Login
        ├── componentes/      # Escaner, Layout, FormProducto, SelectorProducto, ListaMovimientos, etc.
        ├── formato.ts        # números, moneda y fechas con Intl ('es')
        ├── inventario.ts     # motivos por tipo y vista previa del stock resultante
        └── tipos.ts
```

## Modelo de datos

Cuatro tablas. Usa `NUMERIC(12,3)` para cantidades y `NUMERIC(12,2)` para precios. Nunca `float`.

**usuario**
- `id` serial PK
- `nombre` text
- `correo` text único
- `clave_hash` text
- `rol` text: `ADMIN` | `USUARIO`
- `activo` bool, por defecto true
- `creado_en` timestamptz

**categoria**
- `id` serial PK
- `nombre` text único

**producto**
- `id` serial PK
- `codigo` text único (el código de barras)
- `nombre` text
- `presentacion` text nullable (p. ej. "1.5 L", "400 ml")
- `categoria_id` FK nullable
- `unidad` text: `UNIDAD` | `KG` | `LITRO` | `CAJA`
- `precio_compra` numeric(12,2) ≥ 0
- `precio_venta` numeric(12,2) ≥ 0
- `stock` numeric(12,3), por defecto 0, `CHECK (stock >= 0)`
- `stock_minimo` numeric(12,3), por defecto 0
- `nota` text nullable
- `activo` bool
- `creado_en`, `actualizado_en` timestamptz

**movimiento**
- `id` serial PK
- `producto_id` FK
- `usuario_id` FK
- `tipo` text: `ENTRADA` | `SALIDA`
- `motivo` text. Entradas: `COMPRA`, `DEVOLUCION`, `AJUSTE`. Salidas: `USO`, `VENTA`, `PERDIDA`, `AJUSTE`. Las anulaciones usan `ANULACION`
- `cantidad` numeric(12,3) > 0
- `precio_unitario` numeric(12,2)
- `stock_despues` numeric(12,3)
- `comentario` text nullable
- `pedido` text nullable (n.º de pedido)
- `responsable` text nullable (cliente o quien recibe/entrega)
- `anula_a` FK a movimiento, nullable
- `fecha` timestamptz, por defecto now()
- Índice en `(producto_id, fecha)`

## Reglas de negocio (no negociables)

1. **Solo `servicios/inventario.py` modifica `producto.stock`.** Ningún router ni otro módulo lo cambia directamente.
2. Registrar un movimiento ocurre en **una transacción**: `SELECT ... FOR UPDATE` sobre el producto, validar, insertar el movimiento con `stock_despues`, actualizar `producto.stock`, commit.
3. El stock **nunca queda negativo**. Una salida mayor al stock devuelve 409 con el mensaje `"Stock insuficiente: quedan {stock} {unidad}"`.
4. Los movimientos **no se editan ni se borran**. Para corregir, un ADMIN anula: se crea el movimiento contrario con `motivo = ANULACION` y `anula_a` apuntando al original. Un movimiento solo se puede anular una vez, y una anulación no se puede anular.
5. En una entrada, `precio_unitario` es el precio de compra (por defecto `producto.precio_compra`). En una salida, es el precio de venta (por defecto `producto.precio_venta`). Una entrada puede actualizar opcionalmente `producto.precio_compra`, solo si quien la registra es ADMIN.
6. Solo ADMIN crea, edita o desactiva productos, categorías y usuarios, y cambia precios. USUARIO ve todo y registra entradas y salidas.
7. Los productos no se borran: se desactivan (`activo = false`).
8. El código de barras es único. Al escanear un código que no existe, el frontend ofrece crear el producto (solo ADMIN).
9. Los permisos se validan **siempre en el backend**; el frontend solo oculta botones.

## API

Prefijo `/api`. JSON. Errores con forma `{"detail": "mensaje en español"}`.

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/auth/login` | — | correo + clave → access token; refresh en cookie |
| POST | `/auth/refresh` | — | renueva el access token |
| POST | `/auth/logout` | todos | borra la cookie |
| GET | `/auth/yo` | todos | usuario actual |
| GET/POST | `/usuarios` | ADMIN | listar / crear |
| PATCH | `/usuarios/{id}` | ADMIN | editar, cambiar rol, desactivar |
| GET/POST | `/categorias` | GET todos, POST ADMIN | |
| PATCH | `/categorias/{id}` | ADMIN | |
| GET | `/productos?q=&categoria_id=&bajo_minimo=&activo=` | todos | búsqueda por nombre o código |
| GET | `/productos/codigo/{codigo}` | todos | resolver un código escaneado; 404 si no existe |
| GET | `/productos/{id}` | todos | |
| POST | `/productos` | ADMIN | |
| PATCH | `/productos/{id}` | ADMIN | no permite cambiar `stock` |
| GET | `/productos/{id}/movimientos` | todos | historial del producto |
| GET | `/movimientos?desde=&hasta=&tipo=&producto_id=` | todos | paginado |
| POST | `/movimientos` | todos | `{producto_id, tipo, motivo, cantidad, precio_unitario?, comentario?, pedido?, responsable?, actualizar_precio?}` |
| POST | `/movimientos/{id}/anular` | ADMIN | |
| GET | `/resumen` | todos | total productos, valor a compra, valor a venta, productos bajo mínimo, últimos 10 movimientos |
| GET | `/reportes/stock.xlsx` | todos | stock con precios y valor total |
| GET | `/reportes/movimientos.xlsx?desde=&hasta=` | todos | |

Los precios y valores se muestran a USUARIO (solo lectura).

## Pantallas

- **Login.**
- **Inicio:** botón grande "Escanear", tarjetas con total de productos, valor del inventario (compra y venta) y cantidad bajo mínimo; lista de productos bajo mínimo; últimos movimientos; botones "Entrada" y "Salida".
- **Productos:** buscador (acepta escribir o escanear), filtro por categoría, lista con nombre, código, stock, unidad y precio de venta. Marca en rojo los que están bajo mínimo.
- **Ficha de producto:** datos, precios, stock, botones Entrada/Salida, historial. ADMIN puede editar.
- **Entrada / Salida:** producto (escaneado o buscado), cantidad, precio (prellenado), motivo, comentario. Muestra el stock resultante antes de confirmar.
- **Historial:** todos los movimientos con filtros y botón "Descargar Excel". ADMIN ve "Anular".
- **Ajustes (ADMIN):** usuarios y categorías.

Diseño **mobile-first**: botones de al menos 44 px, formularios de una columna, navegación inferior en celular y lateral en pantallas anchas. Formato de números y moneda con `Intl.NumberFormat('es')`.

## Escáner

- Componente `componentes/Escaner.tsx` con `BrowserMultiFormatReader` de `@zxing/browser`, cámara trasera, formatos EAN-13, EAN-8, UPC-A, UPC-E y Code-128.
- Al leer un código: vibración corta si está disponible, se detiene la cámara y se llama a `GET /productos/codigo/{codigo}`.
- Siempre debe existir la alternativa de escribir el código a mano.
- Los lectores USB/Bluetooth escriben el código y un Enter en el buscador: tratar Enter en el campo de código como un escaneo.
- La cámara requiere HTTPS (en local, `localhost` sirve).

## Configuración

Variables de entorno del backend (`backend/.env`, con un `.env.example` en el repo):

```
DATABASE_URL=postgresql+psycopg://bodega:bodega@localhost:5434/bodega
JWT_SECRET=genera-uno-con-openssl-rand-hex-32
CORS_ORIGINS=http://localhost:5173
ADMIN_CORREO=admin@bodega.local
ADMIN_CLAVE=cambia-esto
COOKIE_SEGURA=false   # true en producción (HTTPS): la cookie del refresh lleva Secure
```

Al arrancar, si no existe ningún usuario, se crea el ADMIN con `ADMIN_CORREO` y `ADMIN_CLAVE`.

Frontend (`frontend/.env`): `VITE_API_URL=/api`. El frontend siempre llama a la API en su mismo dominio: en local, el proxy de `vite.config.ts` envía `/api` a `localhost:8000`; en producción, el rewrite de `frontend/vercel.json` lo envía a Render. Así la cookie del refresh es propia del dominio (no de terceros) y no hace falta CORS.

Nunca subas archivos `.env` ni secretos al repositorio.

## Comandos

```bash
# Base de datos local
docker compose up -d

# Backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload       # http://localhost:8000/docs
uv run pytest
uv run ruff check . && uv run ruff format .

# Frontend
cd frontend
npm install
npm run dev                                 # http://localhost:5173
npm run test
npm run lint && npm run build
```

Importar el Excel de inventario anterior (hojas Inventario y Movimientos): `uv run python -m app.importar_excel archivo.xlsx` muestra el plan; con `--aplicar` lo guarda. No importa dos veces los mismos códigos.

Cada cambio al modelo va con una migración de Alembic (`uv run alembic revision --autogenerate -m "..."`), revisada a mano.

## Pruebas mínimas obligatorias

En `backend/tests/`, contra una base PostgreSQL de prueba:
- Una entrada suma stock y guarda `stock_despues` correcto.
- Una salida mayor al stock devuelve 409 y no cambia nada.
- Anular una entrada resta el stock; anular dos veces falla.
- USUARIO recibe 403 al crear productos, cambiar precios o anular.
- `GET /productos/codigo/{codigo}` devuelve 404 para un código inexistente.
- El valor del inventario en `/resumen` coincide con la suma de stock × precio.

## Plan del MVP (en este orden)

1. Estructura del repo, `docker-compose.yml`, backend con `/api/salud`, frontend con Vite y Tailwind.
2. Modelos, primera migración, usuario ADMIN inicial.
3. Auth (login, refresh, logout, roles) y pantalla de login.
4. Categorías y productos (backend + pantallas).
5. Servicio de inventario, movimientos y anulación, con sus pruebas.
6. Escáner integrado en Inicio, Productos y Entrada/Salida.
7. Resumen e Inicio con alertas de stock bajo y valor del inventario.
8. Historial y exportación a Excel.
9. PWA instalable, ajustes de usuarios.
10. Despliegue: Neon, Render (`uv run alembic upgrade head` antes de arrancar), Vercel (ajustar la URL de Render en `frontend/vercel.json`).

## Fuera de alcance (no implementar sin que se pida)

Varias bodegas, ubicaciones, lotes, vencimientos, proveedores, órdenes de compra, facturación, fotos, modo sin conexión, notificaciones, conteo físico, historial de precios.

Para crecer más adelante: varias bodegas = tabla `bodega` + `bodega_id` en `movimiento` y stock por bodega. Diseña el servicio de inventario de forma que ese cambio sea local a él.

## Documento de diseño

Análisis completo (requerimientos, historias de usuario, diagramas): https://claude.ai/artifact/HjcqrNKAuC3qjNCtGHqjCZ
