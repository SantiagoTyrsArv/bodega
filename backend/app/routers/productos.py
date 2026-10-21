from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import ProductoCrear, ProductoEditar, ProductoSalida
from app.modelos import Categoria, Producto
from app.seguridad import AdminActual, UsuarioActual

router = APIRouter(prefix="/productos", tags=["productos"])

Db = Annotated[Session, Depends(get_db)]

# Campos que no pueden quedar vacíos al editar
OBLIGATORIOS = {"codigo", "nombre", "unidad", "precio_compra", "precio_venta", "stock_minimo"}


def _obtener(db: Session, producto_id: int) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El producto no existe")
    return producto


def _validar_codigo_libre(db: Session, codigo: str, excepto_id: int | None = None) -> None:
    consulta = select(Producto.id).where(Producto.codigo == codigo)
    if excepto_id is not None:
        consulta = consulta.where(Producto.id != excepto_id)
    if db.scalar(consulta) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Ya existe un producto con el código {codigo}"
        )


def _validar_categoria(db: Session, categoria_id: int | None) -> None:
    if categoria_id is not None and db.get(Categoria, categoria_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La categoría no existe")


@router.get("")
def listar(
    _: UsuarioActual,
    db: Db,
    q: str | None = None,
    categoria_id: int | None = None,
    bajo_minimo: bool = False,
    activo: bool = True,
) -> list[ProductoSalida]:
    consulta = select(Producto).where(Producto.activo == activo).order_by(Producto.nombre)
    if q and q.strip():
        patron = f"%{q.strip()}%"
        consulta = consulta.where(or_(Producto.nombre.ilike(patron), Producto.codigo.ilike(patron)))
    if categoria_id is not None:
        consulta = consulta.where(Producto.categoria_id == categoria_id)
    if bajo_minimo:
        # Bajo mínimo: tiene un mínimo definido y el stock llegó a él o está por debajo
        consulta = consulta.where(
            Producto.stock_minimo > 0, Producto.stock <= Producto.stock_minimo
        )
    return [ProductoSalida.model_validate(p) for p in db.scalars(consulta)]


@router.get("/codigo/{codigo}")
def por_codigo(codigo: str, _: UsuarioActual, db: Db) -> ProductoSalida:
    producto = db.scalar(select(Producto).where(Producto.codigo == codigo.strip()))
    if producto is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"No existe un producto con el código {codigo}"
        )
    return ProductoSalida.model_validate(producto)


@router.get("/{producto_id}")
def detalle(producto_id: int, _: UsuarioActual, db: Db) -> ProductoSalida:
    return ProductoSalida.model_validate(_obtener(db, producto_id))


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(datos: ProductoCrear, _: AdminActual, db: Db) -> ProductoSalida:
    _validar_codigo_libre(db, datos.codigo)
    _validar_categoria(db, datos.categoria_id)
    producto = Producto(**datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return ProductoSalida.model_validate(producto)


@router.patch("/{producto_id}")
def editar(producto_id: int, datos: ProductoEditar, _: AdminActual, db: Db) -> ProductoSalida:
    producto = _obtener(db, producto_id)
    cambios = datos.model_dump(exclude_unset=True)
    for campo in OBLIGATORIOS & cambios.keys():
        if cambios[campo] is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, f"Dato inválido en '{campo}'"
            )
    if "codigo" in cambios:
        _validar_codigo_libre(db, cambios["codigo"], excepto_id=producto_id)
    if "categoria_id" in cambios:
        _validar_categoria(db, cambios["categoria_id"])
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return ProductoSalida.model_validate(producto)
