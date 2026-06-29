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

        if not cpf or not nome:
            continue

        rows.append({
            "nome": nome,
            "cpf": cpf,
            "funcao": funcao,
            "setor": setor,
            "matricula": matricula,
        })

    return rows


async def run(path: str) -> None:
    engine = create_async_engine(settings.database_url)
    funcionarios = import_excel(path)
    print(f"Total de registros no Excel: {len(funcionarios)}")

    inserted = 0
    skipped = 0
    async with engine.begin() as conn:
        for f in funcionarios:
            result = await conn.execute(
                text("""
                    INSERT INTO public.usuarios (nome, cpf, funcao, setor, matricula)
                    VALUES (:nome, :cpf, :funcao, :setor, :matricula)
                    ON CONFLICT (cpf) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        funcao = EXCLUDED.funcao,
                        setor = EXCLUDED.setor,
                        matricula = EXCLUDED.matricula
                """),
                f,
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
