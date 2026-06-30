from typing import Any

from pydantic import BaseModel


class PerguntaOpcaoRead(BaseModel):
    id: str
    categoria: str
    pergunta: str
    tipo: str
    opcoes: list[dict[str, Any]]
    ordem: int


class PerguntaPreferenciaRead(BaseModel):
    id: str
    categoria: str
    pergunta: str
    tipo: str
    opcoes: list[dict[str, Any]]
    peso: int
    ordem: int


class PerguntaCulturaRead(BaseModel):
    id: str
    categoria: str
    pergunta: str
    tipo: str
    opcoes: list[dict[str, Any]]
    ordem: int
