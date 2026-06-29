from datetime import datetime

from pydantic import BaseModel, Field


class SetorCreate(BaseModel):
    nome: str = Field(min_length=1)


class SetorUpdate(BaseModel):
    nome: str = Field(min_length=1)


class SetorRead(BaseModel):
    id: int
    nome: str
    created_at: datetime | None = None


class SetorSummary(SetorRead):
    quantidade_senhas: int = 0
    senhas_respondidas: int = 0
