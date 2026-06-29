# Pesquisa Corporativa API

Primeira versão da API FastAPI para retirar a regra de negocio do frontend Vue e centralizar o acesso ao banco Supabase/PostgreSQL.

## Decisões da primeira versão

- Reutiliza o schema Supabase atual sem migrations destrutivas.
- Usa FastAPI, SQLAlchemy 2.x async, Pydantic v2 e Alembic.
- Mantem compatibilidade com os fluxos atuais: login por senha, setores, senhas, perguntas, respostas de opcoes e preferencias.
- Move para services da API as regras de geração de senha, validação de quantidade, upsert de respostas, verificação de gravação, conclusão de formulario e cálculo de pesos da pesquisa preferencial.

## Como rodar

```bash
cd api
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Depois acesse `http://127.0.0.1:8000/docs`.

## Variáveis principais

- `DATABASE_URL`: conexão PostgreSQL/Supabase em formato `postgresql+asyncpg://...`.
- `ALLOWED_ORIGINS`: origens do frontend separadas por virgula.
- `ADMIN_EMAIL` e `ADMIN_PASSWORD`: credenciais administrativas temporarias para preservar o comportamento atual.

## Observação de segurança

O frontend ainda expõe a anon key do Supabase e o SQL atual possui RLS aberta para `anon`. A migração deve, em fases posteriores, mover todas as chamadas para a API, retirar o acesso direto do browser ao banco e revisar as policies.
