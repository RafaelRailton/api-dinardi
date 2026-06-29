#!/bin/sh
set -e

echo "Rodando migrations..."
alembic upgrade head

echo "Rodando seed..."
python scripts/seed.py

echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
