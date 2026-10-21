from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.esquemas import LoginEntrada, TokenSalida, UsuarioSalida
from app.modelos import Usuario
from app.seguridad import (
    UsuarioActual,
    crear_access_token,
    crear_refresh_token,
    leer_token,
    verificar_clave,
)

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_REFRESH = "refresh_token"
# La cookie solo viaja a las rutas de auth, no en cada petición
RUTA_COOKIE = "/api/auth"


def _poner_cookie(respuesta: Response, usuario_id: int) -> None:
    settings = get_settings()
    respuesta.set_cookie(
        COOKIE_REFRESH,
        crear_refresh_token(usuario_id),
        max_age=settings.refresh_dias * 24 * 3600,
        path=RUTA_COOKIE,
        httponly=True,
        secure=settings.cookie_segura,
        # Con HTTPS y dominios distintos (Vercel + Render) se necesita "none"
        samesite="none" if settings.cookie_segura else "lax",
    )


def _respuesta_token(respuesta: Response, usuario: Usuario) -> TokenSalida:
    _poner_cookie(respuesta, usuario.id)
    return TokenSalida(
        access_token=crear_access_token(usuario.id),
        usuario=UsuarioSalida.model_validate(usuario),
    )


@router.post("/login")
def login(
    datos: LoginEntrada, respuesta: Response, db: Annotated[Session, Depends(get_db)]
) -> TokenSalida:
    usuario = db.scalar(select(Usuario).where(Usuario.correo == datos.correo.strip().lower()))
    # Mismo mensaje para correo inexistente, clave mala o usuario inactivo
    if (
        usuario is None
        or not usuario.activo
        or not verificar_clave(datos.clave, usuario.clave_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o clave incorrectos")
    return _respuesta_token(respuesta, usuario)


@router.post("/refresh")
def refresh(
    respuesta: Response,
    db: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenSalida:
    usuario_id = leer_token(refresh_token, "refresh") if refresh_token else None
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None or not usuario.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión expirada, vuelve a ingresar")
    # Se renueva también la cookie: la sesión dura mientras se use
    return _respuesta_token(respuesta, usuario)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(respuesta: Response) -> None:
    # No exige access token: así se puede cerrar sesión aunque haya expirado
    settings = get_settings()
    respuesta.delete_cookie(
        COOKIE_REFRESH,
        path=RUTA_COOKIE,
        httponly=True,
        secure=settings.cookie_segura,
        samesite="none" if settings.cookie_segura else "lax",
    )


@router.get("/yo")
def yo(usuario: UsuarioActual) -> UsuarioSalida:
    return UsuarioSalida.model_validate(usuario)
