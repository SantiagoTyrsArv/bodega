from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.modelos import Rol, Usuario
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

api = APIRouter(prefix="/api")


@api.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


app.include_router(api)
