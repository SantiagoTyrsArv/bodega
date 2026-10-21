from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import MovimientoEntrada, MovimientoSalida, PaginaMovimientos
from app.modelos import Movimiento, TipoMovimiento
from app.seguridad import AdminActual, UsuarioActual
from app.servicios import inventario

router = APIRouter(prefix="/movimientos", tags=["movimientos"])

Db = Annotated[Session, Depends(get_db)]


def listar_movimientos(
    db: Session,
    *,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    tipo: TipoMovimiento | None = None,
    producto_id: int | None = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> PaginaMovimientos:
    """Movimientos del más reciente al más antiguo. desde es inclusivo y hasta exclusivo."""
    filtros = []
    if desde is not None:
        filtros.append(Movimiento.fecha >= desde)
    if hasta is not None:
        filtros.append(Movimiento.fecha < hasta)
    if tipo is not None:
        filtros.append(Movimiento.tipo == tipo)
    if producto_id is not None:
        filtros.append(Movimiento.producto_id == producto_id)

    total = db.scalar(select(func.count()).select_from(Movimiento).where(*filtros)) or 0
    consulta = (
        select(Movimiento)
        .where(*filtros)
        .order_by(Movimiento.fecha.desc(), Movimiento.id.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
    )
    items = [MovimientoSalida.model_validate(m) for m in db.scalars(consulta)]
    return PaginaMovimientos(items=items, total=total, pagina=pagina, por_pagina=por_pagina)


@router.get("")
def listar(
    _: UsuarioActual,
    db: Db,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    tipo: TipoMovimiento | None = None,
    producto_id: int | None = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaginaMovimientos:
    return listar_movimientos(
        db,
        desde=desde,
        hasta=hasta,
        tipo=tipo,
        producto_id=producto_id,
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def registrar(datos: MovimientoEntrada, usuario: UsuarioActual, db: Db) -> MovimientoSalida:
    try:
        movimiento = inventario.registrar_movimiento(db, usuario=usuario, **datos.model_dump())
    except inventario.ErrorInventario as e:
        raise HTTPException(e.estado, e.mensaje) from None
    return MovimientoSalida.model_validate(movimiento)


@router.post("/{movimiento_id}/anular", status_code=status.HTTP_201_CREATED)
def anular(movimiento_id: int, admin: AdminActual, db: Db) -> MovimientoSalida:
    try:
        movimiento = inventario.anular_movimiento(db, movimiento_id=movimiento_id, usuario=admin)
    except inventario.ErrorInventario as e:
        raise HTTPException(e.estado, e.mensaje) from None
    return MovimientoSalida.model_validate(movimiento)
