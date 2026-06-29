from datetime import datetime

from pydantic import BaseModel, Field


class SenhaRead(BaseModel):
    id: int
    senha: str
    setor_id: int
    formulario_opcoes_concluido: bool
    formulario_preferencias_concluido: bool
    formulario_opcoes_concluido_em: datetime | None = None
    formulario_preferencias_concluido_em: datetime | None = None
    created_at: datetime | None = None


class GenerateSenhasRequest(BaseModel):
    setor_id: int
    quantidade: int = Field(default=1, ge=1, le=500)


class GenerateSenhasResponse(BaseModel):
    setor_id: int
    senhas: list[SenhaRead]
