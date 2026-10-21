from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.modelos import Rol, Usuario

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)
ALGORITMO = "HS256"


def hashear_clave(clave: str) -> str:
    return _hasher.hash(clave)


def verificar_clave(clave: str, clave_hash: str) -> bool:
    try:
        return _hasher.verify(clave_hash, clave)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _crear_token(usuario_id: int, tipo: str, duracion: timedelta) -> str:
    ahora = datetime.now(UTC)
    datos = {"sub": str(usuario_id), "tipo": tipo, "iat": ahora, "exp": ahora + duracion}
    return jwt.encode(datos, get_settings().jwt_secret, algorithm=ALGORITMO)


def crear_access_token(usuario_id: int) -> str:
    return _crear_token(usuario_id, "access", timedelta(minutes=get_settings().access_minutos))


def crear_refresh_token(usuario_id: int) -> str:
    return _crear_token(usuario_id, "refresh", timedelta(days=get_settings().refresh_dias))


def leer_token(token: str, tipo: str) -> int | None:
    """Devuelve el id del usuario si el token es válido y del tipo esperado."""
    try:
        datos = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITMO])
    except jwt.InvalidTokenError:
        return None
    if datos.get("tipo") != tipo:
        return None
    return int(datos["sub"])


def _no_autenticado(mensaje: str = "Sesión no válida o expirada") -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, mensaje, headers={"WWW-Authenticate": "Bearer"}
    )


def usuario_actual(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    """Dependencia: exige un access token válido de un usuario activo."""
    if credenciales is None:
        raise _no_autenticado("No autenticado")
    usuario_id = leer_token(credenciales.credentials, "access")
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    # Se consulta la base en cada petición para que desactivar a alguien tenga efecto inmediato
    if usuario is None or not usuario.activo:
        raise _no_autenticado()
    return usuario


def requiere_admin(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
    """Dependencia: exige rol ADMIN."""
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo un administrador puede hacer esto")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]
AdminActual = Annotated[Usuario, Depends(requiere_admin)]
