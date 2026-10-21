from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.modelos import Rol, Usuario
from app.routers import auth, categorias, productos
from app.seguridad import hashear_clave

settings = get_settings()


def crear_admin_inicial(db: Session) -> bool:
    """Crea el ADMIN con ADMIN_CORREO y ADMIN_CLAVE si no existe ningún usuario."""
    if db.scalar(select(exists().select_from(Usuario))):
        return False
    db.add(
        Usuario(
            nombre="Administrador",
            correo=settings.admin_correo.strip().lower(),
            clave_hash=hashear_clave(settings.admin_clave),
            rol=Rol.ADMIN,
        )
    )
    db.commit()
    return True


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        crear_admin_inicial(db)
    yield


app = FastAPI(title="BODEGA API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.lista_cors,
    allow_credentials=True,  # necesario para la cookie del refresh token
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def error_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Errores de validación con la forma {"detail": "mensaje en español"}."""
    error = exc.errors()[0]
    campo = ".".join(str(p) for p in error["loc"] if p not in ("body", "query", "path"))
    mensaje = f"Dato inválido en '{campo}'" if campo else "Datos inválidos"
    return JSONResponse(status_code=422, content={"detail": mensaje})


api = APIRouter(prefix="/api")


@api.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


api.include_router(auth.router)
api.include_router(categorias.router)
api.include_router(productos.router)
app.include_router(api)
