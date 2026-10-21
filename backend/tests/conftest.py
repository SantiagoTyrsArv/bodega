import os

# Configuración de pruebas: se fija antes de importar la app para no tocar la base de desarrollo
URL_PRUEBAS = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://bodega:bodega@localhost:5434/bodega_test"
)
os.environ["DATABASE_URL"] = URL_PRUEBAS
os.environ["JWT_SECRET"] = "secreto-de-pruebas-de-al-menos-32-caracteres"
os.environ["ADMIN_CORREO"] = "admin@prueba.local"
os.environ["ADMIN_CLAVE"] = "clave-admin"
os.environ["COOKIE_SEGURA"] = "false"

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modelos import Rol, Usuario  # noqa: E402
from app.seguridad import hashear_clave  # noqa: E402

CLAVE = "clave-de-prueba"


@pytest.fixture(scope="session", autouse=True)
def base_de_pruebas() -> Iterator[None]:
    """Crea la base de pruebas si no existe y aplica las migraciones."""
    url = make_url(URL_PRUEBAS)
    servidor = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with servidor.connect() as conexion:
        existe = conexion.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database}
        )
        if not existe:
            conexion.execute(text(f'CREATE DATABASE "{url.database}"'))
    servidor.dispose()
    command.upgrade(Config("alembic.ini"), "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def limpiar_tablas() -> Iterator[None]:
    yield
    with engine.begin() as conexion:
        conexion.execute(
            text("TRUNCATE movimiento, producto, categoria, usuario RESTART IDENTITY CASCADE")
        )


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as sesion:
        yield sesion


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    # El "with" ejecuta el arranque de la app (crea el ADMIN inicial)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def crear_usuario(db: Session) -> Callable[..., Usuario]:
    def _crear(correo: str, rol: Rol = Rol.USUARIO, activo: bool = True) -> Usuario:
        usuario = Usuario(
            nombre=correo.split("@")[0],
            correo=correo,
            clave_hash=hashear_clave(CLAVE),
            rol=rol,
            activo=activo,
        )
        db.add(usuario)
        db.commit()
        return usuario

    return _crear


@pytest.fixture
def headers_de(cliente: TestClient) -> Callable[[str], dict[str, str]]:
    """Inicia sesión y devuelve el header Authorization."""

    def _headers(correo: str, clave: str = CLAVE) -> dict[str, str]:
        r = cliente.post("/api/auth/login", json={"correo": correo, "clave": clave})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _headers
