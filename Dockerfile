FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY scripts ./scripts
COPY ["ListadeFunc15062026 Pesquisa Cultura.xlsx", "./"]

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir . && \
    chmod +x scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["scripts/entrypoint.sh"]
