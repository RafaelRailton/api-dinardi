from pydantic import BaseModel, field_validator

from app.utils.cpf import is_valid_cpf


class RespondentLoginRequest(BaseModel):
    cpf: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not is_valid_cpf(v):
            raise ValueError("CPF invalido")
        return v


class RespondentSession(BaseModel):
    is_logged_in: bool = True
    senha_id: int
    senha_codigo: str
    setor_id: int
    setor_nome: str
    formulario_opcoes_concluido: bool
    formulario_preferencias_concluido: bool


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminSession(BaseModel):
    is_logged_in: bool = True
    email: str
