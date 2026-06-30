"""Importa a planilha de funcionarios para a tabela usuarios."""

import asyncio
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


def normalize_cpf(raw: str | int) -> str:
    digits = re.sub(r"\D", "", str(raw))
    return digits.zfill(11)


def import_excel(path: str) -> list[dict]:
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("openpyxl nao instalado. Execute: pip install openpyxl")

    wb = openpyxl.load_workbook(path)
    ws = wb.active

    rows = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if row[9] is None:
            continue
        cpf = normalize_cpf(row[9])
        nome = (row[1] or "").strip()
        funcao = (row[3] or "").strip()
        setor = (row[4] or "").strip()
        matricula = str(int(row[0])) if row[0] is not None else None

        dt_admissao = None
        if row[5] is not None:
            from datetime import datetime, date
            if isinstance(row[5], datetime):
                dt_admissao = row[5].date()
            elif isinstance(row[5], date):
                dt_admissao = row[5]
            else:
                dt_admissao = datetime.strptime(str(row[5]), "%Y-%m-%d").date()

        unidade = str(int(row[6])) if row[6] is not None else None
        sexo = str(row[10]).strip() if row[10] is not None else None

        if not cpf or not nome:
            continue

        rows.append({
            "nome": nome,
            "cpf": cpf,
            "funcao": funcao,
            "setor": setor,
            "matricula": matricula,
            "data_contratacao": dt_admissao,
            "unidade": unidade,
            "sexo": sexo,
        })

    return rows


async def run(path: str) -> None:
    engine = create_async_engine(settings.database_url)
    funcionarios = import_excel(path)
    print(f"Total de registros no Excel: {len(funcionarios)}")

    inserted = 0
    skipped = 0
    setores_cache: dict[str, int] = {}
    async with engine.begin() as conn:
        for f in funcionarios:
            setor_id = None
            if f["setor"]:
                setor_nome = f["setor"]
                setor_id = setores_cache.get(setor_nome)
                if setor_id is None:
                    setor_result = await conn.execute(
                        text("""
                            INSERT INTO public.setores (nome)
                            VALUES (:nome)
                            ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome
                            RETURNING id
                        """),
                        {"nome": setor_nome},
                    )
                    setor_id = setor_result.scalar_one()
                    setores_cache[setor_nome] = setor_id

            result = await conn.execute(
                text("""
                    INSERT INTO public.usuarios (nome, cpf, funcao, setor, setor_id, matricula, data_contratacao, unidade, sexo)
                    VALUES (:nome, :cpf, :funcao, :setor, :setor_id, :matricula, :data_contratacao, :unidade, :sexo)
                    ON CONFLICT (cpf) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        funcao = EXCLUDED.funcao,
                        setor = EXCLUDED.setor,
                        setor_id = EXCLUDED.setor_id,
                        matricula = EXCLUDED.matricula,
                        data_contratacao = EXCLUDED.data_contratacao,
                        unidade = EXCLUDED.unidade,
                        sexo = EXCLUDED.sexo
                """),
                {**f, "setor_id": setor_id},
            )
            if setor_id is not None:
                await conn.execute(
                    text("""
                        UPDATE public.senhas
                        SET setor_id = :setor_id
                        WHERE senha = :cpf
                    """),
                    {"setor_id": setor_id, "cpf": f["cpf"]},
                )
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

    await engine.dispose()
    print(f"Importacao concluida: {inserted} inseridos/atualizados, {skipped} ignorados")


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "ListadeFunc15062026 Pesquisa Cultura.xlsx"
    asyncio.run(run(path))
