from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class OpcaoRespostaInput(BaseModel):
    pergunta_id: str
    resposta: int
    data_resposta: datetime | None = None


class OpcaoSubmitRequest(BaseModel):
    senha_id: int
    setor_id: int
    respostas: list[OpcaoRespostaInput] = Field(min_length=1)


class PreferenciaPesoInput(BaseModel):
    pergunta_id: str
    resposta: int | str
    data_resposta: datetime | None = None


class PreferenciaPesosSubmitRequest(BaseModel):
    senha_id: int
    setor_id: int
    respostas: list[PreferenciaPesoInput] = Field(min_length=1)


class PreferenciaClassificacaoSubmitRequest(BaseModel):
    senha_id: int
    setor_id: int
    mais20: list[str] = Field(min_length=20, max_length=20)
    mais10: list[str] = Field(min_length=10, max_length=10)
    menos20: list[str] = Field(min_length=20, max_length=20)
    menos10: list[str] = Field(min_length=10, max_length=10)

    @field_validator("mais20", "mais10", "menos20", "menos10")
    @classmethod
    def ensure_unique(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("A lista de selecao nao pode conter perguntas repetidas.")
        return value


class FormularioSubmitResponse(BaseModel):
    senha_id: int
    formulario: str
    total_respostas: int
    concluido: bool
