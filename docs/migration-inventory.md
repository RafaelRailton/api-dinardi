# Inventario inicial da migracao Vue 3 + Supabase para FastAPI

Data: 2026-06-26

## Estrutura Vue analisada

- `interface/src/router/index.js`: rotas `Home`, `LoginAdmin`, `LoginRespondente`, `Admin`, `Participante`, `Formulario`, `Preferencias`, `Conclusao` e `Debug`.
- `interface/src/supabase.js`: cria o client Supabase com URL e anon key no frontend; contem `generatePassword` e `isValidPassword`.
- `interface/src/stores/auth.js`: login do respondente por senha, sessão em `localStorage`, refresh do status dos formularios e logout.
- `interface/src/stores/questionnaire.js`: estado do formulario de opcoes, carregamento de perguntas, progresso local, upsert de respostas e conclusão.
- `interface/src/views/PreferenciasView.vue`: fluxo da pesquisa preferencial, regras de seleção e cálculo de pesos.
- `interface/src/views/AdminView.vue`: controle administrativo e exportação CSV/XLSX.
- `interface/src/components/admin/SetorList.vue`: CRUD de setores e contagem de senhas respondidas.
- `interface/src/components/admin/SenhaList.vue`: geração, listagem e exclusão de senhas.
- `interface/src/data/perguntasOpcoes.js` e `interface/src/data/perguntasPreferencias.js`: fallback local de perguntas.

## Modelo de banco atual

Fonte: `interface/supabase-schema-corrigido.sql`.

- `setores`: setores/departamentos.
- `senhas`: credenciais anonimas por setor, com flags de conclusão dos formularios.
- `perguntas_opcoes`: perguntas do formulario de opcoes.
- `respostas_opcoes`: respostas inteiras por senha, setor e pergunta; unico por `senha_id, pergunta_id`.
- `perguntas_preferencias`: afirmacoes de preferencias com peso base.
- `respostas_preferencias`: pesos finais por senha, setor e pergunta; unico por `senha_id, pergunta_id`.
- `progresso_respondente`: progresso server-side previsto no schema, mas o frontend atual usa principalmente `localStorage`.

## Regras de negocio encontradas

- Respondente informa uma senha de 8 caracteres; busca é feita com `senha.toUpperCase()`.
- Login de respondente carrega setor e flags de conclusão.
- Admin atual usa credenciais fixas no frontend: `admin@sistema.com / admin123`.
- Senhas geradas possuem 8 caracteres usando `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`.
- Quantidade de senhas geradas deve ficar entre 1 e 500.
- Setor não pode ter nome vazio.
- Formulario de opcoes carrega perguntas do banco por `ordem`; caso falhe, frontend usa fallback local.
- Respostas de opcoes são gravadas com upsert por `senha_id, pergunta_id`.
- Após gravar opcoes, o frontend verifica se todas as perguntas esperadas foram persistidas.
- Ao concluir opcoes, `senhas.formulario_opcoes_concluido` vira `true` e `formulario_opcoes_concluido_em` recebe timestamp.
- Pesquisa preferencial tem 46 itens com peso inicial 3.
- Fluxo preferencial atual:
  - selecionar 20 mais importantes: peso 4;
  - selecionar 10 dentro das 20 mais importantes: peso 5;
  - selecionar 20 menos importantes: se peso ainda for 3, muda para 2; se ja foi marcado como importante, vira 0;
  - selecionar 10 dentro das 20 menos importantes: se peso for 2, muda para 1; caso contrario, permanece 0.
- Pesos finais de preferencias são gravados como texto em `respostas_preferencias.resposta`.
- Após gravar preferencias, o frontend verifica quantidade e pesos salvos antes de marcar conclusão.
- Exportação administrativa combina setores, senhas e respostas dos dois formularios em linhas planas para CSV/XLSX.

## Fluxos da aplicação

1. Respondente
   - Login por senha.
   - Dashboard com dois formularios obrigatorios.
   - Formulario de opcoes.
   - Persistência das respostas.
   - Marcação de conclusão.
   - Formulario de preferencias.
   - Persistência dos pesos finais.
   - Marcação de conclusão.

2. Administrador
   - Login administrativo simples.
   - Gerenciamento de setores.
   - Gerenciamento de senhas por setor.
   - Exportação consolidada de resultados.

## Casos de uso iniciais

- Autenticar respondente por senha.
- Atualizar status do respondente.
- Autenticar admin.
- Listar, criar, editar e excluir setores.
- Listar, gerar e excluir senhas.
- Listar perguntas de opcoes.
- Listar perguntas de preferencias.
- Enviar respostas de opcoes.
- Calcular e enviar classificação preferencial.
- Enviar pesos finais de preferencias.
- Exportar respostas consolidadas.

## Segurança e riscos

- A anon key do Supabase está exposta no frontend.
- Policies RLS permitem leitura ampla e escrita anonima em tabelas sensiveis.
- Admin usa credencial fixa no frontend.
- Sessões são apenas flags em `localStorage`.
- Qualquer cliente com anon key pode consultar respostas e senhas enquanto as policies atuais permanecerem abertas.

## Recomendações de performance

- Consolidar exportação em endpoint backend para evitar múltiplas consultas grandes no browser.
- Trocar contagem de senhas por setor por agregação SQL no backend.
- Evitar verificação pós-gravação com roundtrips repetidos no frontend; manter transação no backend.
- Considerar índices compostos por `setor_id, senha_id` nas respostas se os relatórios crescerem.

## Plano de migração

### Fase 1 - Inventário

Objetivo: mapear frontend, Supabase e regras existentes.
Arquivos: `interface/src`, `interface/supabase-schema-corrigido.sql`, `api/docs`.
Riscos: regras implícitas em UI não cobertas.
Checklist: rotas, stores, views, componentes admin e schema analisados.
Critério de aceite: documentação revisada e divergências registradas.

### Fase 2 - API inicial

Objetivo: criar camada FastAPI sobre o banco atual.
Arquivos: `api/app`, `api/pyproject.toml`, `api/.env.example`.
Riscos: diferenças entre validações do frontend e backend.
Checklist: endpoints de auth, setores, senhas, perguntas e respostas.
Critério de aceite: API sobe e documentação OpenAPI lista os fluxos principais.

### Fase 3 - Migração gradual do frontend

Objetivo: substituir chamadas Supabase por HTTP para a API.
Arquivos: stores e views que importam `supabase`.
Riscos: sessão local e estados parciais.
Checklist: migrar `auth`, `questionnaire`, `PreferenciasView`, admin.
Critério de aceite: frontend não faz escrita direta no Supabase.

### Fase 4 - Segurança

Objetivo: remover segredos e permissões abertas do browser.
Arquivos: policies Supabase, autenticação API, variáveis de ambiente.
Riscos: bloquear acessos ainda usados pelo frontend durante transição.
Checklist: JWT/session, admin seguro, RLS restrita.
Critério de aceite: anon key não consegue ler/escrever dados sensiveis diretamente.

### Fase 5 - Testes e deploy

Objetivo: cobrir regras e publicar API.
Arquivos: `api/tests`, pipeline, configuração de deploy.
Riscos: comportamento diferente em produção.
Checklist: testes de services, integração com banco, smoke test frontend.
Critério de aceite: fluxos de respondente e admin passam ponta a ponta.
