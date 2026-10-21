from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modelos import Rol


class LoginEntrada(BaseModel):
    correo: str = Field(min_length=3)
    clave: str = Field(min_length=1)


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol: Rol
    activo: bool
    creado_en: datetime


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSalida
