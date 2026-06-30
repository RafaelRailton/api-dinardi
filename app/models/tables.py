from datetime import date, datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Setor(Base):
    __tablename__ = "setores"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    senhas: Mapped[list["Senha"]] = relationship(back_populates="setor")


class Senha(Base):
    __tablename__ = "senhas"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    senha: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    setor_id: Mapped[int] = mapped_column(ForeignKey("public.setores.id", ondelete="CASCADE"))
    usuario_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("public.usuarios.id", ondelete="CASCADE")
    )
    formulario_opcoes_concluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formulario_preferencias_concluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formulario_cultura_concluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formulario_opcoes_concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    formulario_preferencias_concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    formulario_cultura_concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    setor: Mapped[Setor] = relationship(back_populates="senhas")
    usuario: Mapped["Usuario | None"] = relationship()


class PerguntaOpcao(Base):
    __tablename__ = "perguntas_opcoes"
    __table_args__ = {"schema": "public"}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    categoria: Mapped[str] = mapped_column(Text, nullable=False)
    pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    opcoes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)


class RespostaOpcao(Base):
    __tablename__ = "respostas_opcoes"
    __table_args__ = (
        UniqueConstraint("senha_id", "pergunta_id", name="respostas_opcoes_unique_resposta"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    senha_id: Mapped[int] = mapped_column(ForeignKey("public.senhas.id", ondelete="CASCADE"))
    setor_id: Mapped[int] = mapped_column(ForeignKey("public.setores.id", ondelete="CASCADE"))
    pergunta_id: Mapped[str] = mapped_column(ForeignKey("public.perguntas_opcoes.id", ondelete="RESTRICT"))
    resposta: Mapped[int] = mapped_column(Integer, nullable=False)
    data_resposta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PerguntaPreferencia(Base):
    __tablename__ = "perguntas_preferencias"
    __table_args__ = {"schema": "public"}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    categoria: Mapped[str] = mapped_column(Text, nullable=False)
    pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    opcoes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    peso: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)


class RespostaPreferencia(Base):
    __tablename__ = "respostas_preferencias"
    __table_args__ = (
        UniqueConstraint("senha_id", "pergunta_id", name="respostas_preferencias_unique_resposta"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    senha_id: Mapped[int] = mapped_column(ForeignKey("public.senhas.id", ondelete="CASCADE"))
    setor_id: Mapped[int] = mapped_column(ForeignKey("public.setores.id", ondelete="CASCADE"))
    pergunta_id: Mapped[str] = mapped_column(
        ForeignKey("public.perguntas_preferencias.id", ondelete="RESTRICT")
    )
    resposta: Mapped[str] = mapped_column(Text, nullable=False)
    data_resposta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    cpf: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    funcao: Mapped[str | None] = mapped_column(Text)
    setor: Mapped[str | None] = mapped_column(Text)
    setor_id: Mapped[int | None] = mapped_column(ForeignKey("public.setores.id", ondelete="RESTRICT"), nullable=True)
    matricula: Mapped[str | None] = mapped_column(Text)
    data_contratacao: Mapped[date | None] = mapped_column(Date)
    unidade: Mapped[str | None] = mapped_column(Text)
    sexo: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    setor_rel: Mapped["Setor"] = relationship()


class ProgressoRespondente(Base):
    __tablename__ = "progresso_respondente"
    __table_args__ = (
        UniqueConstraint("senha_id", "formulario"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    senha_id: Mapped[int] = mapped_column(ForeignKey("public.senhas.id", ondelete="CASCADE"))
    formulario: Mapped[str] = mapped_column(Text, nullable=False)
    respostas: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    pergunta_atual: Mapped[int] = mapped_column(Integer, default=0)
    concluido: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PerguntaCultura(Base):
    __tablename__ = "perguntas_cultura"
    __table_args__ = {"schema": "public"}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    categoria: Mapped[str] = mapped_column(Text, nullable=False)
    pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    opcoes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)


class RespostaCultura(Base):
    __tablename__ = "respostas_cultura"
    __table_args__ = (
        UniqueConstraint("senha_id", "pergunta_id", name="respostas_cultura_unique_resposta"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    senha_id: Mapped[int] = mapped_column(ForeignKey("public.senhas.id", ondelete="CASCADE"))
    setor_id: Mapped[int] = mapped_column(ForeignKey("public.setores.id", ondelete="CASCADE"))
    pergunta_id: Mapped[str] = mapped_column(
        ForeignKey("public.perguntas_cultura.id", ondelete="RESTRICT")
    )
    resposta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    data_resposta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
