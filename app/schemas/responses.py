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
    rounds: list[list[str]]

    @field_validator("rounds")
    @classmethod
    def validate_4_rounds(cls, value: list[list[str]]) -> list[list[str]]:
        if len(value) != 4:
            raise ValueError("Devem ser exatamente 4 rodadas.")

        if not (2 <= len(value[0]) <= 20):
            raise ValueError("Rodada 1 deve ter entre 2 e 20 itens.")

        expected2 = len(value[0]) // 2
        if len(value[1]) != expected2:
            raise ValueError(f"Rodada 2 deve ter {expected2} itens (metade de {len(value[0])}).")
        if not set(value[1]).issubset(set(value[0])):
            raise ValueError("Rodada 2 deve ser subconjunto da rodada 1.")

        if not (2 <= len(value[2]) <= 20):
            raise ValueError("Rodada 3 deve ter entre 2 e 20 itens.")

        expected4 = len(value[2]) // 2
        if len(value[3]) != expected4:
            raise ValueError(f"Rodada 4 deve ter {expected4} itens (metade de {len(value[2])}).")
        if not set(value[3]).issubset(set(value[2])):
            raise ValueError("Rodada 4 deve ser subconjunto da rodada 3.")

        for i, ids in enumerate(value):
            if len(set(ids)) != len(ids):
                raise ValueError(f"Rodada {i + 1} contem itens duplicados.")

        return value


class FormularioSubmitResponse(BaseModel):
    senha_id: int
    formulario: str
    total_respostas: int
    concluido: bool


class CulturaRespostaValores(BaseModel):
    atual: int


class CulturaRespostaInput(BaseModel):
    pergunta_id: str
    resposta: dict[str, CulturaRespostaValores]
    data_resposta: datetime | None = None

    @field_validator("resposta")
    @classmethod
    def validate_alternativas(cls, value: dict[str, CulturaRespostaValores]) -> dict[str, CulturaRespostaValores]:
        if set(value.keys()) != {"A", "B", "C", "D"}:
            raise ValueError("Devem existir exatamente as alternativas A, B, C e D")
        for key, val in value.items():
            if not (0 <= val.atual <= 100):
                raise ValueError(f"Alternativa {key}: atual deve estar entre 0 e 100")
            if not isinstance(val.atual, int):
                raise ValueError(f"Alternativa {key}: valores devem ser inteiros")

        soma_atual = sum(v.atual for v in value.values())
        if soma_atual != 100:
            raise ValueError(f"Soma da coluna Atual deve ser 100 (atual: {soma_atual})")
        return value


class CulturaSubmitRequest(BaseModel):
    senha_id: int
    setor_id: int
    respostas: list[CulturaRespostaInput] = Field(min_length=1)


class CulturaPerfilScore(BaseModel):
    perfil: str
    nome: str
    atual: float


class CulturaResultadoResponse(BaseModel):
    senha_id: int
    scores: list[CulturaPerfilScore]
    perfil_dominante_atual: str


class CulturaSubmitResponse(FormularioSubmitResponse):
    resultado: CulturaResultadoResponse | None = None


class CulturaRespostaSalva(BaseModel):
    pergunta_id: str
    resposta: dict[str, CulturaRespostaValores]
    data_resposta: datetime | None = None


class CulturaSalvarRequest(BaseModel):
    senha_id: int
    setor_id: int
    pergunta_id: str
    resposta: dict[str, int]
