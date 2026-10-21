from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import CategoriaEntrada, CategoriaSalida
from app.modelos import Categoria
from app.seguridad import AdminActual, UsuarioActual

router = APIRouter(prefix="/categorias", tags=["categorias"])

Db = Annotated[Session, Depends(get_db)]


def _validar_nombre_libre(db: Session, nombre: str, excepto_id: int | None = None) -> None:
    consulta = select(Categoria.id).where(func.lower(Categoria.nombre) == nombre.lower())
    if excepto_id is not None:
        consulta = consulta.where(Categoria.id != excepto_id)
    if db.scalar(consulta) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese nombre")


@router.get("")
def listar(_: UsuarioActual, db: Db) -> list[CategoriaSalida]:
    categorias = db.scalars(select(Categoria).order_by(Categoria.nombre))
    return [CategoriaSalida.model_validate(c) for c in categorias]


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(datos: CategoriaEntrada, _: AdminActual, db: Db) -> CategoriaSalida:
    _validar_nombre_libre(db, datos.nombre)
    categoria = Categoria(nombre=datos.nombre)
    db.add(categoria)
    db.commit()
    return CategoriaSalida.model_validate(categoria)


@router.patch("/{categoria_id}")
def editar(categoria_id: int, datos: CategoriaEntrada, _: AdminActual, db: Db) -> CategoriaSalida:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La categoría no existe")
    _validar_nombre_libre(db, datos.nombre, excepto_id=categoria_id)
    categoria.nombre = datos.nombre
    db.commit()
    return CategoriaSalida.model_validate(categoria)
