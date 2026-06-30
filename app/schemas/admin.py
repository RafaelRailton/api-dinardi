from pydantic import BaseModel, field_validator

from app.utils.cpf import is_valid_cpf


class ExportRow(BaseModel):
    setor: str
    senha: str
    respostas: dict[str, str | int | None]


class SetorDashboard(BaseModel):
    setor_id: int
    setor_nome: str
    total_usuarios: int
    respostas_opcoes: int
    respostas_preferencias: int
    respostas_cultura: int = 0
    pendentes_opcoes: int
    pendentes_preferencias: int
    pendentes_cultura: int = 0


class DashboardResponse(BaseModel):
    setores: list[SetorDashboard]
    total_usuarios: int
    total_respostas_opcoes: int
    total_respostas_preferencias: int
    total_respostas_cultura: int = 0


class RespondenteLog(BaseModel):
    nome: str
    cpf: str
    formulario_opcoes_concluido: bool
    formulario_opcoes_concluido_em: str | None = None
    formulario_preferencias_concluido: bool
    formulario_preferencias_concluido_em: str | None = None
    formulario_cultura_concluido: bool = False
    formulario_cultura_concluido_em: str | None = None


class CriarUsuarioRequest(BaseModel):
    nome: str
    cpf: str
    setor_id: int | None = None
    funcao: str | None = None
    matricula: str | None = None
    data_contratacao: str | None = None
    unidade: str | None = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not is_valid_cpf(v):
            raise ValueError("CPF invalido")
        return v


class CulturaAgregadoPerfil(BaseModel):
    perfil: str
    nome: str
    atual: float


class CulturaAgregadoResponse(BaseModel):
    total_respondentes: int
    scores_medios: list[CulturaAgregadoPerfil]
    perfil_dominante_atual: str
