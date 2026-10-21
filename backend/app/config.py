from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída desde variables de entorno o backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://bodega:bodega@localhost:5434/bodega"
    # Orígenes permitidos separados por coma
    cors_origins: str = "http://localhost:5173"
    # Credenciales del ADMIN que se crea si la base no tiene usuarios. Sin valor por defecto.
    admin_correo: str
    admin_clave: str

    # Mínimo 32 caracteres; generar con: openssl rand -hex 32
    jwt_secret: str = Field(min_length=32)
    access_minutos: int = 15
    refresh_dias: int = 7
    # En producción (HTTPS) va en true: la cookie del refresh solo viaja por HTTPS
    cookie_segura: bool = False

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
