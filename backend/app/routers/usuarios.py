from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import UsuarioCrear, UsuarioEditar, UsuarioSalida
from app.modelos import Usuario
from app.seguridad import AdminActual, hashear_clave

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

Db = Annotated[Session, Depends(get_db)]

CLAVE_MINIMA = 8


def _validar_clave(clave: str) -> None:
    if len(clave) < CLAVE_MINIMA:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"La clave debe tener al menos {CLAVE_MINIMA} caracteres",
        )


def _validar_correo_libre(db: Session, correo: str, excepto_id: int | None = None) -> None:
    consulta = select(Usuario.id).where(Usuario.correo == correo)
    if excepto_id is not None:
        consulta = consulta.where(Usuario.id != excepto_id)
    if db.scalar(consulta) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Ya existe un usuario con el correo {correo}"
        )


@router.get("")
def listar(_: AdminActual, db: Db) -> list[UsuarioSalida]:
    usuarios = db.scalars(select(Usuario).order_by(Usuario.activo.desc(), Usuario.nombre))
    return [UsuarioSalida.model_validate(u) for u in usuarios]


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(datos: UsuarioCrear, _: AdminActual, db: Db) -> UsuarioSalida:
    _validar_clave(datos.clave)
    _validar_correo_libre(db, datos.correo)
    usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        clave_hash=hashear_clave(datos.clave),
        rol=datos.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioSalida.model_validate(usuario)


@router.patch("/{usuario_id}")
def editar(usuario_id: int, datos: UsuarioEditar, admin: AdminActual, db: Db) -> UsuarioSalida:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El usuario no existe")
    cambios = datos.model_dump(exclude_none=True)

    # Un ADMIN no puede dejarse fuera a sí mismo: así siempre queda al menos un ADMIN activo
    if usuario.id == admin.id:
        if cambios.get("activo") is False:
            raise HTTPException(status.HTTP_409_CONFLICT, "No puedes desactivar tu propio usuario")
        if "rol" in cambios and cambios["rol"] != usuario.rol:
            raise HTTPException(status.HTTP_409_CONFLICT, "No puedes cambiar tu propio rol")

    if "correo" in cambios:
        _validar_correo_libre(db, cambios["correo"], excepto_id=usuario_id)
    if "clave" in cambios:
        _validar_clave(cambios["clave"])
        usuario.clave_hash = hashear_clave(cambios.pop("clave"))
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return UsuarioSalida.model_validate(usuario)
