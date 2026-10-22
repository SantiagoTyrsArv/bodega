import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize(
    ("url", "esperada"),
    [
        (
            "postgresql://u:c@host/bd?sslmode=require",
            "postgresql+psycopg://u:c@host/bd?sslmode=require",
        ),
        ("postgres://u:c@host/bd", "postgresql+psycopg://u:c@host/bd"),
        ("postgresql+psycopg://u:c@host/bd", "postgresql+psycopg://u:c@host/bd"),
    ],
)
def test_database_url_usa_psycopg(url: str, esperada: str):
    s = Settings(database_url=url, admin_correo="a@b.c", admin_clave="x", jwt_secret="s" * 32)
    assert s.database_url == esperada


def test_admin_correo_invalido_impide_arrancar():
    with pytest.raises(ValidationError):
        Settings(admin_correo="adminbodega.com", admin_clave="x", jwt_secret="s" * 32)


def test_admin_correo_se_normaliza():
    s = Settings(admin_correo="  Admin@Bodega.COM ", admin_clave="x", jwt_secret="s" * 32)
    assert s.admin_correo == "admin@bodega.com"
