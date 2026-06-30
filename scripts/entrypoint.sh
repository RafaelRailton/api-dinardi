#!/bin/sh
set -e

echo "Rodando migrations..."
alembic upgrade head

echo "Rodando seed..."
python scripts/seed.py

FUNCIONARIOS_EXCEL="${FUNCIONARIOS_EXCEL:-ListadeFunc15062026 Pesquisa Cultura.xlsx}"
echo "Importando funcionarios de ${FUNCIONARIOS_EXCEL}..."
python scripts/import_funcionarios.py "${FUNCIONARIOS_EXCEL}"

echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
