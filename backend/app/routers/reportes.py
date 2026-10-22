from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import ProductoSalida, Resumen
from app.modelos import Producto
from app.routers.movimientos import listar_movimientos
from app.routers.productos import bajo_minimo_sql
from app.seguridad import UsuarioActual

router = APIRouter(tags=["reportes"])

Db = Annotated[Session, Depends(get_db)]


@router.get("/resumen")
def resumen(_: UsuarioActual, db: Db) -> Resumen:
    activos = Producto.activo.is_(True)
    total, valor_compra, valor_venta = db.execute(
        select(
            func.count(),
            func.coalesce(func.sum(Producto.stock * Producto.precio_compra), 0),
            func.coalesce(func.sum(Producto.stock * Producto.precio_venta), 0),
        ).where(activos)
    ).one()
    bajo_minimo = db.scalars(
        select(Producto).where(activos, bajo_minimo_sql()).order_by(Producto.nombre)
    )
    centavo = Decimal("0.01")
    return Resumen(
        total_productos=total,
        valor_compra=Decimal(valor_compra).quantize(centavo),
        valor_venta=Decimal(valor_venta).quantize(centavo),
        bajo_minimo=[ProductoSalida.model_validate(p) for p in bajo_minimo],
        ultimos_movimientos=listar_movimientos(db, por_pagina=10).items,
    )
