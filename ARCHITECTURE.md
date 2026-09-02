# ARCHITECTURE.md — Arquitetura comprovada/documentada

## A. Finalidade e escopo

Este documento mapeia a arquitetura **real, observada em código e configuração**
neste repositório, no momento da auditoria de governança. Ele não substitui
`AGENTS.md` (regras de conduta) nem `DECISIONS.md` (decisões humanas) — não
decide nenhuma pendência arquitetural, apenas a descreve.

Toda afirmação aqui segue a disciplina de `AGENTS.md`, Seção 8, e é rotulada
por tipo:

- **[estrutura existente]** — código/arquivo/módulo confirmado no repositório;
- **[integração existente]** — conexão implementada entre componentes internos
  ou com serviço externo;
- **[dependência externa]** — serviço de terceiro do qual o sistema depende;
- **[feature flag]** — comportamento controlado por variável de ambiente,
  observado como configurável;
- **[risco]** — característica arquitetural que representa risco identificado
  na auditoria;
- **[pendência humana]** — ponto que depende de decisão humana, referenciado
  sem ID até `DECISIONS.md` existir.

`ROADMAP.md` não autoriza alteração arquitetural, e este documento não a
decide — apenas descreve o que existe.

## B. Visão geral do sistema

SaaS jurídico com backend Python/FastAPI e frontend React/Vite, banco
PostgreSQL, autenticação JWT, isolamento multi-tenant (com RLS em Postgres),
e um conjunto de serviços de domínio jurídico (análise, diagnóstico,
especialização de minutas, relatórios/PDF) organizados em módulos por área.
Nomenclatura oficial do produto é **[pendência humana]**.

## C. Frontend

**[estrutura existente]** React 19 + Vite 8 (`frontend/package.json`), com
diretórios `src/{assets,components,pages,config,services,types}` e um
subdiretório `components/expansion`. Existe uma pasta `frontend/dist` com
artefatos de build gerados, observados no checkout auditado. **A existência
desse diretório demonstra apenas isso** — a presença de artefatos de build no
checkout auditado. Ela **não comprova, por si só**: que esse build corresponde
ao código corrente; que passou pelo CI; que está implantado em algum
ambiente; ou que corresponde à versão atualmente servida em Production.
Nenhum build foi executado nesta etapa para verificar essa correspondência.
Este documento **não aprofunda** a arquitetura interna do frontend (rotas,
estado, componentes) além dessa estrutura de alto nível — isso não foi
auditado em detalhe nesta sessão; aprofundamento é limite declarado na
Seção Q.

## D. Backend / API

**[estrutura existente]** FastAPI, com `app.main` como ponto de entrada e
rotas versionadas sob `API_V1_PREFIX = /api/v1` (`core/settings.py`).
Camadas observadas em `backend/app/`:

- `api/v1/routes/`: `auth`, `admin`, `billing`, `webhooks`, `cases`,
  `case_timeline`, `case_attachments`, `case_contact_logs`,
  `case_evidence_checklist`, `case_operational_assistant`,
  `case_party_states`, `editable_documents`, `appeal_reaction_states`,
  `legal_modules`, `usage`, `health`.
- `core/`: `settings.py` (configuração + fail-fast production-like),
  `tenant.py` (RLS), `security.py`, `middleware.py`, `redact.py`, `plans.py`,
  `subscription.py`, `context.py`, `logging.py`.
- `db/`: sessão e base do SQLAlchemy.
- `schemas/`: contratos Pydantic de entrada/saída.
- `services/`: lógica de negócio (ver Seções E–K).
- `modules/`: módulos de domínio jurídico (ver Seção E).
- `alembic/`: migrações de banco versionadas.

**[integração existente]** Rotas dependem de `db/session.py` via injeção de
dependência (`Depends(get_db)`), padrão consistente em toda a API observada.

## E. Domínio jurídico e motores

**[estrutura existente]** `backend/app/modules/`:

- `engines/` — `registry.py` + `base.py`, com subpastas `trabalhista` e
  `civil_ambiental`: padrão de motor de análise plugável por área jurídica.
- `legal_editor/` — `contracts.py` + `service.py`: montagem/edição de peças.
- `document_factory/` — `contracts.py`, `intake.py`, `service.py`: intake e
  estruturação de dados do caso.
- `parties_succession/` — `contracts.py` + `service.py`: transições de estado
  das partes do caso (`case_party_state`). O campo `source` desse fluxo tem
  semântica oficial já documentada em `docs/PROJECT_RULES.md` (contrato
  arquitetural válido, não bug).
- `appeals_reactions/` e `jobs/` — `contracts.py` + `service.py` cada;
  presentes no repositório, mas **não foram lidos em profundidade nesta
  auditoria** (limite declarado na Seção Q).

Registro de módulos jurídicos: `services/legal_modules.py` +
`api/v1/routes/legal_modules.py`.

## F. Copiloto / editor assistido

**[estrutura existente] [risco]** `services/case_operational_assistant.py`
— **arquivo de ~7.600 linhas**, de longe o maior do backend (o segundo maior
serviço observado tem 542 linhas). Concentra a lógica de especialização de
minutas por área jurídica e tipo de ação (ex.: função
`_build_editor_all_blocks_action_specialization`, observada na frente local
aberta, com ramo `civil_professional_risk_restriction_claim`).

Este arquivo é registrado aqui como **risco arquitetural de manutenção e de
regressão silenciosa** (concentração de lógica crítica em um único módulo).
**Nenhuma refatoração é decidida ou autorizada por este documento** — é
**[pendência humana]**, já registrada em `AGENTS.md`/`PROJECT_STATE.md`/
`ROADMAP.md`.

Padrão observado no código gerado por esse serviço (confirmado no diff da
frente local revisado nesta sessão): instruções explícitas para não presumir
fatos, provas, dano ou nexo causal sem suporte documental, e para distinguir
dado confirmado de pendência — coerente com o princípio jurídico central de
`AGENTS.md`, Seção 2.

## G. Persistência e multi-tenancy

**[estrutura existente]** SQLAlchemy + Alembic sobre PostgreSQL. Modelos
observados em `backend/app/models/`: `tenant`, `tenant_member`, `user`,
`case`, `case_analysis`, `case_attachment`, `case_contact_log`,
`case_evidence_checklist`, `case_party_state`, `case_timeline`,
`editable_document`, `appeal_reaction_state`, `billing_request`,
`subscription`, `tenant_usage_event`, `usage_counter`, `audit_log`,
`business_audit_log`.

**[integração existente]** Isolamento multi-tenant via `core/tenant.py`:
`set_tenant_on_session` executa `SELECT set_config('app.tenant_id', ...)` na
conexão ativa para habilitar RLS no Postgres; é **no-op explícito em SQLite**
(usado nos testes por padrão — ver Seção M). `scoped_query` filtra
explicitamente por `tenant_id` no nível de aplicação, como camada adicional
ao RLS de banco.

**[estrutura existente]** Anexos de caso são armazenados em sistema de
arquivos local, segregado por tenant:
`backend/storage/case_attachments/tenant_<id>/`
(`CASE_ATTACHMENT_STORAGE_DIR` em `core/settings.py`). **Nenhum storage de
objeto externo (S3 ou equivalente) foi observado** nesta auditoria.

## H. Autenticação / autorização

**[estrutura existente]** JWT (`PyJWT`), `passlib` para hashing de senha,
`AUTH_ENABLED`/`AUTH_PROTECT_DOCS` como flags de configuração. Rota de
bootstrap `POST /api/v1/auth/seed-admin` é **break-glass** condicionada a
`ALLOW_SEED_ADMIN=true` + `ADMIN_SEED_TOKEN` real (documentado em
`docs/BREAK_GLASS.md` e reforçado por `validate_production_settings()` em
`core/settings.py`, que falha o boot em ambiente production-like se essas
condições não forem atendidas).

**[feature flag]** `AUTH_PROTECT_DOCS=true` em ambiente production-like fecha
`/docs`, `/redoc` e `/openapi.json` (comportamento descrito no `README.md` e
consistente com o fail-fast observado em `settings.py`).

## I. IA / LLM

**[estrutura existente] [integração existente]** `services/llm_client.py`:
cliente HTTP (via `httpx`) para provider `openai`, construindo requisição ao
endpoint `responses` e extraindo JSON estruturado da resposta. Provider é
validado explicitamente — qualquer valor de `LLM_PROVIDER` diferente de
`"openai"` levanta erro (`LLMClientError`).

**[feature flag] [dependência externa]** `LLM_ANALYSIS_ENABLED` controla se
essa análise por LLM real está ativa; **valor padrão observado no código é
`false`**. `LLM_API_KEY`, `LLM_MODEL` (default `gpt-5-mini` no código),
`LLM_TIMEOUT_SECONDS`, `LLM_BASE_URL` são configuráveis via ambiente. Este
documento **não verificou ao vivo** se essa integração está ativa em nenhum
ambiente — apenas que o código a suporta quando habilitada.

## J. Documentos / relatórios / PDF

**[estrutura existente]** Componentes implementados que suportam o fluxo
executivo documentado caso → análise → diagnóstico/decisão → resumo →
relatório → PDF: `ai_case_analysis.py`, `analysis_foundations.py`,
`decision_engine.py`, `strategic_diagnosis.py`, `viability_engine.py`,
`executive_summary_engine.py`, `report_engine.py`, `pdf_executive.py`. O
README e demais documentos do projeto descrevem esse fluxo, e há testes
associados na suíte do projeto (ver `MVP_VALIDATION_MATRIX.md`, seções 4–6).
**Esta auditoria não afirma ter rastreado cada chamada runtime ponta a ponta
entre todos esses componentes** — apenas que os componentes existem, que o
fluxo está documentado e que há cobertura de teste associada, salvo onde
explicitamente observado em código nesta sessão. Geração de PDF via
WeasyPrint/fpdf2 (citado no `README.md`; não confirmado em detalhe de código
nesta sessão). `editor_export_service.py` cuida de exportação de documentos
editáveis.

## K. Billing / Asaas

**[integração existente] — A. Entrada/webhook (auditado em detalhe):**
`api/v1/routes/webhooks.py` implementa `POST /webhooks/asaas`, com
verificação de token via comparação segura (`hmac.compare_digest`) contra
`ASAAS_WEBHOOK_TOKEN`, processando eventos
`PAYMENT_RECEIVED`/`PAYMENT_CONFIRMED`/`PAYMENT_UPDATED` com status pago,
vinculando ao `billing_request` pelo `externalReference`. Modelos
`billing_request` e `subscription` confirmados.

**[estrutura existente] [dependência externa] — B. Criação de cobrança/checkout
externo (parcialmente auditado):** `services/payment_checkout.py` normaliza o
provider a partir de `PAYMENT_PROVIDER` (default `"manual"` no código) e
implementa, em detalhe confirmado, o fluxo de checkout `manual`. A
configuração para Asaas existe (`ASAAS_API_KEY`, `ASAAS_BASE_URL` — default
observado é o sandbox `https://api-sandbox.asaas.com/v3`), mas **o caminho
completo de criação de cobrança pela API real do Asaas não foi auditado em
detalhe nesta sessão** — limite declarado na Seção Q.

Portanto, "Asaas" **não** é tratado aqui como integração genérica totalmente
comprovada — apenas o lado A (webhook de entrada) foi auditado em detalhe; o
lado B (criação de cobrança) é [dependência externa] com configuração
existente, não com o ciclo completo verificado nesta auditoria.

**📄 Documentado como produção** (não verificado ao vivo por este documento):
`docs/HANDOFF_FINAL_PRODUCAO_2026-04-28.md` afirma configuração de produção
do Asaas, webhook ativo e um pagamento Pix real confirmado.

## L. Auditoria / logs / segurança

**[estrutura existente]** `services/audit_service.py`, modelos `audit_log` e
`business_audit_log`, `core/middleware.py` (middleware de auditoria HTTP,
citado no `README.md`), `core/redact.py` (redação de dados sensíveis em log).
`AUDIT_EXCLUDE_PATHS` como configuração de exclusão de rotas do log
(`core/settings.py`).

**[risco]** Existência de múltiplos arquivos `.env.bak*` na raiz do
repositório de produto — tratado como risco de higiene a verificar
futuramente (**[pendência humana]**), sem que nenhum conteúdo tenha sido lido
ou exposto por este documento ou por qualquer etapa desta auditoria.

## M. Testes / CI

**[estrutura existente]** 79 arquivos de teste em `backend/tests/`. A maioria
roda contra **SQLite em memória** via `conftest.py` (fixture `db_session` com
`StaticPool`), onde o RLS de `core/tenant.py` é explicitamente no-op. Testes
de isolamento (`test_rls_isolation.py`, `test_tenant_isolation.py`,
`test_multi_tenant_isolation.py`) dependem de **PostgreSQL real** — daí a
necessidade do `docker-compose` local na porta `55432` observada nesta sessão
(ver `PROJECT_STATE.md`, Seção D).

**[integração existente]** `.github/workflows/ci.yml` roda em push/PR para
`main`, com três jobs: `smoke-backend` (migrations Alembic + smoke de auth),
`contract-saas-limits` (contrato de limites de plano) e
`frontend-classifier-and-build`, todos com serviço PostgreSQL 15 no runner.

## N. Infraestrutura e ambientes

**[estrutura existente]** Ambiente local: PostgreSQL 16-alpine via
`docker-compose.yml`, porta host `55432` → container `5432`, healthcheck via
`pg_isready`. Nenhuma outra infraestrutura local (cache, fila, storage
externo) foi observada no `docker-compose.yml`.

**📄 Documentado como produção** (não verificado ao vivo por este documento,
e nenhuma verificação ao vivo em Production está autorizada nesta etapa):
`docs/HANDOFF_FINAL_PRODUCAO_2026-04-28.md` cita hospedagem via Railway e um
serviço de banco Postgres gerenciado nomeado (`Postgres-CLzE - trabalhista`).
`core/settings.py` implementa fail-fast de configuração quando `APP_ENV`
indica `prod`/`production`/`staging` — isso é uma **[estrutura existente]**
de proteção no código, não confirmação de que está ativa em produção real.

## O. Riscos arquiteturais

- **[risco]** `case_operational_assistant.py` monolítico (~7.600 linhas) —
  ver Seção F.
- **[risco]** Documentação do projeto fragmentada entre 50+ arquivos em
  `docs/`, sem índice único até a criação desta governança.
- **[risco]** Armazenamento de anexos em filesystem local por tenant, sem
  storage externo observado — implica dependência de persistência de disco
  do ambiente de execução.
- **[risco]** Caminho de criação de cobrança via API real do Asaas não foi
  lido em detalhe nesta auditoria — zona de incerteza registrada, não
  afirmação de falha.

## P. Decisões humanas pendentes relacionadas à arquitetura

As pendências abaixo já estão formalizadas com IDs `P-*` em `DECISIONS.md`,
que é a fonte normativa para seu estado. São referenciadas aqui apenas para
contexto arquitetural; este documento não resolve nenhuma delas:

- Refatoração (ou não) de `case_operational_assistant.py` — `P-003`.
- Eventual adoção de storage externo para anexos, caso o volume/ambiente
  justifique — `P-009`.
- Nível de aprofundamento de auditoria futura sobre `frontend/`,
  `modules/jobs`, `modules/appeals_reactions` e o caminho de checkout/cobrança
  Asaas via API real — `P-010`.
- Nomenclatura oficial do produto (afeta apenas nomeação, não estrutura) —
  `P-001`.

## Q. Limites do que este documento NÃO comprova

- Não comprova nenhum estado ao vivo de Production — nenhuma verificação ao
  vivo foi realizada; tudo rotulado "documentado como produção" é apenas
  citação de documentação histórica do próprio projeto.
- Não aprofunda a arquitetura interna do `frontend/` (rotas, gerenciamento de
  estado, componentes) além da estrutura de diretórios observada.
- Não confirma o conteúdo detalhado de `modules/jobs` e
  `modules/appeals_reactions` além de sua existência estrutural.
- Não confirma o caminho exato de criação de cobrança via API do Asaas
  (apenas o consumo de webhook e o fluxo `manual` foram lidos em detalhe).
- Não confirma que **toda** minuta ou análise gerada em uso real passou por
  revisão do advogado — essa é uma exigência de processo e produto
  **documentada** (`docs/PRODUTO_OFICIAL.md`, `docs/CRIMINAL_MODULE_V1_SCOPE.md`,
  `AGENTS.md` Seção 2), não uma garantia automática verificada por este
  documento.
- Não expõe, e não expôs em nenhum momento desta auditoria, conteúdo de
  `.env`/`.env.bak*` ou qualquer segredo.
- Não decide nenhuma das pendências humanas listadas na Seção P.

## R. Diagrama textual de alto nível (somente relações comprovadas)

```
Frontend (React 19 + Vite 8)
        │  relação arquitetural observada/documentada (HTTP/JSON);
        │  sem validação end-to-end em Production por esta auditoria
        ▼
Backend API — FastAPI, /api/v1 (rotas em api/v1/routes/)
        │
        ├── core/ (settings, tenant/RLS, security, middleware, redact)
        │
        ├── services/ — componentes que suportam o fluxo executivo
        │              documentado (analysis → diagnosis/decision → summary
        │              → report → pdf_executive); cadeia de chamadas runtime
        │              ponta a ponta não rastreada integralmente nesta
        │              auditoria
        │
        ├── services/case_operational_assistant.py (copiloto/editor;
        │              risco arquitetural — Seção F)
        │
        ├── modules/ (engines, legal_editor, document_factory,
        │              parties_succession, appeals_reactions, jobs)
        │
        ├── services/llm_client.py ──[feature flag LLM_ANALYSIS_ENABLED]──▶
        │                                    OpenAI API [dependência externa,
        │                                    não verificada ao vivo]
        │
        ├── api/v1/routes/webhooks.py ──▶ Asaas [webhook de ENTRADA
        │        observado/auditado em detalhe]
        │
        ├── services/payment_checkout.py ──▶ Asaas [criação de cobrança via
        │        API externa NÃO auditada em detalhe; apenas fluxo manual
        │        confirmado]
        │
        ├── SQLAlchemy ORM ──▶ PostgreSQL (RLS por tenant_id via
        │                       set_config('app.tenant_id', ...))
        │
        └── Filesystem local ──▶ storage/case_attachments/tenant_<id>/

CI (GitHub Actions) ──▶ PostgreSQL 15 (container efêmero de teste,
                          não relacionado ao banco de produção)

Production (Railway + Postgres gerenciado) — citado apenas em documentação
histórica do projeto; não verificado ao vivo por este documento.
```
