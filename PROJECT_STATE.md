# PROJECT_STATE.md — Checkpoint documental

## A. Natureza deste checkpoint

Este documento **não é** a fonte de verdade do estado do Git ou do código. É um
registro datado de valores **observados** em um momento específico, conforme
definido em `AGENTS.md` (Seção 9). Toda nova sessão deve obter branch, HEAD,
`origin/main` e status do working tree diretamente via comandos git — nunca a
partir deste arquivo.

- **Checkpoint registrado em:** 2026-09-01
- **Contexto do checkpoint:** implantação inicial da governança persistente
  (`AGENTS.md` → `PROJECT_STATE.md` → `ROADMAP.md` → `ARCHITECTURE.md` →
  `DECISIONS.md` → `NEXT_STEP.md` → `CLAUDE.md`) neste repositório.
- **Atualização registrada em:** 2026-09-02 — fechamento da frente de
  produto `P-007` (código/produto integrado a `main` via PR #306; fechamento
  documental integrado via PR #307) e decisão humana
  sobre `P-002` (registrada em `DECISIONS.md` como `OPS-004`). Ver Seções
  C, H e I abaixo para o estado observado nesta data.
- **Atualização registrada em:** 2026-09-24 — reconciliação documental com a
  auditoria-mestra somente leitura realizada nesta data sobre o HEAD
  `0fc0755d7de4ced50400f6e297a99338f6d9cd50`. Ver "PAINEL MESTRE" e Seções
  D, E, G e I abaixo. `P-002` passa a constar como resolvida **apenas como
  prioridade** (`OPS-004`), com as decisões técnicas A e B pendentes.
- **Atualização registrada em:** 2026-09-25 — registro documental das
  decisões humanas (DICO/ChatGPT) sobre os itens A e B de `OPS-004`:
  **A1** (`ARCH-001`: RLS PostgreSQL real e versionado + isolamento de
  aplicação mantido) e **B2** (`ARCH-002`: `limits_for(plan_type)` como
  fonte oficial; `Subscription.case_limit` legado/informativo). Base: HEAD
  observado `55945775ffeda2a8ea5c033bd8569d156f0972ac` (`main` =
  `origin/main` local, após PR #308) e investigação somente leitura da
  semântica do limite administrativo. Nenhum código, teste, banco ou
  migration alterado; nenhum teste executado. Ver "PAINEL MESTRE" e Seções
  D, G e I abaixo.
- **Atualização registrada em:** 2026-09-25 — registro documental da
  decisão humana (DICO/ChatGPT) sobre o modelo de execução **BLOCO 1A →
  BLOCO 2 → BLOCO 1B** (`OPS-005`), tomada após relatório somente leitura
  de preparação do BLOCO 1. Base: HEAD observado
  `ba169bcaadb9836dd9763f96ba818a7544d37ea8` (`main` = `origin/main`
  local, após PR #309, que integrou o adendo A1/B2). Nenhum código,
  teste, workflow, banco ou migration alterado; nenhum teste executado.
- Este checkpoint só deve ser atualizado quando houver mudança material de
  estado, houver evidência objetiva, rastreável e válida para o estado relevante
  do código — inclusive evidência de checkpoint anterior quando continuar válida
  pelos critérios de `AGENTS.md` Seção 7 —, a atualização fizer parte de tarefa
  autorizada e forem respeitadas as regras de aprovação de `AGENTS.md`. Memória
  de agente ou afirmação de conversa nunca substitui evidência.

## PAINEL MESTRE

Painel-resumo permanente deste checkpoint. Os valores abaixo são
**observados em data específica** e devem ser atualizados a cada checkpoint
autorizado; não substituem a verificação direta do Git (Seção B) nem
`DECISIONS.md`/`NEXT_STEP.md`.

- **Último checkpoint Git observado (2026-09-29):** antes da criação desta
  branch documental, `main` local e `origin/main` estavam sincronizados em
  `1e7a686c602621ab5eaa86fdc9aaf3edd99e7833` (PR #313). A reconciliação
  documental corrente ocorre na branch
  `docs/reconcile-ops005-completion-v1`.
- **OPS-005 — sequência obrigatória concluída com evidência no Git:**
  - **BLOCO 1A:** PR #311,
    `c75d2e6c9a503bb1db7b76a690097b355bab7fa2` — infraestrutura de testes
    backend tornada hermética, incluindo PostgreSQL de teste, configuração
    de pytest e suporte específico aos testes PostgreSQL;
  - **BLOCO 2:** PR #312,
    `29f7bd45b729766417781a80d7dfff56ddb3aa49` — RLS PostgreSQL tenant
    implementado/versionado, com migration, integração de tenant/session,
    segurança e testes associados;
  - **BLOCO 1B:** PR #313,
    `1e7a686c602621ab5eaa86fdc9aaf3edd99e7833` — suíte backend completa
    incorporada ao CI; `backend-full-suite` tornou-se status check
    obrigatório.
- **Baseline final registrado do BLOCO 1B:** `316 passed, 0 failed`,
  `112 warnings`.
- **Estado atual comprovado nesta frente:** infraestrutura hermética de
  testes, RLS PostgreSQL tenant e suíte backend completa no CI estão
  concluídos. As estimativas percentuais da auditoria-mestra anterior são
  históricas e **não são recalculadas automaticamente por este checkpoint**.
- **Continuam fora do fechamento de OPS-005:** semântica de
  `remaining.cases`/`cases_per_month` (congelada, dependente de decisão
  humana futura), rate limiting, políticas LGPD formais, pendências de
  frontend, gate formal de release e demais decisões abertas.
- **Production:** **NÃO VERIFICADA** neste checkpoint e não foi tocada pela
  reconciliação documental.
- **Próximo passo:** concluir esta reconciliação documental. Qualquer nova
  frente técnica depende de auditoria/proposta e autorização humana
  específica; a conclusão de OPS-005 não autoriza automaticamente o próximo
  bloco.
- **Decisões humanas abertas:** `P-001`, `P-003`, `P-004`, `P-005`,
  `P-006`, `P-008`, `P-009`, `P-010`.

## B. Git / baseline histórico do checkpoint inicial

- **Repositório de produto original:** `/home/dilsondev/projetos/ia_trabalhista_robusta`
- **Branch histórica observada no checkpoint inicial:** `fix/editor-civil-professional-risk-specialization-v1`
- **Baseline histórico observado/aprovado naquele checkpoint:** `4e9d22fdae99fc717192ea5b6b96214f61d70628`
- **`origin/main` histórico observado naquele checkpoint inicial:** mesmo hash,
  `4e9d22fdae99fc717192ea5b6b96214f61d70628` — confirmado em pré-check de leitura
  antes da criação do worktree de governança.
- Estes valores refletem o que foi observado no momento do checkpoint. **Não
  representam o HEAD atual eterno nem "working tree limpo" permanente.** Uma
  nova sessão deve reobter esses valores via `git status`, `git rev-parse HEAD`
  e `git rev-parse origin/main`.

## C. Frente de produto P-007 — encerrada (histórico preservado)

Em checkpoint anterior (2026-09-01), a branch
`fix/editor-civil-professional-risk-specialization-v1` possuía trabalho
local não commitado em dois arquivos (`case_operational_assistant.py` e
`test_massive_multicase_all_blocks_regression.py`), preservado intacto
durante a implantação da governança em worktree separado. Essa era a
pendência formalizada como `P-007`.

**Estado atual (checkpoint 2026-09-02): P-007 está resolvida.** A frente
foi commitada (`7771de0384d9c9bd56f6ecb62f855674a3d96ed6`), integrada a
`main` via PR #306 (squash-merged, `b9ca8a8141da1a582a0ee2842b9278652e1705f4`),
e a branch de trabalho foi removida local e remotamente somente após prova
de equivalência material de conteúdo com `main`. Detalhes completos da
resolução estão registrados em `DECISIONS.md`, `OPS-003`. `main` local e
`origin/main` estão sincronizadas nesse histórico.

## D. Evidência de testes

- Uma regressão **direcionada** foi executada pelo responsável, **antes desta
  implantação de governança**, com resultado: `108 passed, 24 warnings`.
- Esta evidência é registrada como **regressão direcionada observada/informada
  antes da auditoria de governança**. Ela **não** foi executada pelo Claude
  nesta sessão de auditoria/implantação.
- A execução consolidada compreendeu exatamente estes quatro arquivos:
  - `backend/tests/test_massive_multicase_all_blocks_regression.py`
  - `backend/tests/test_case_operational_assistant_editor_block_routing.py`
  - `backend/tests/test_case_operational_assistant_review_validation.py`
  - `backend/tests/test_editable_documents_flow.py`
  Isso continua sendo uma **regressão direcionada**, e **não** a suíte completa
  de testes do projeto, nem "produto totalmente validado". O teste específico
  `test_civil_professional_risk_edson_uses_specific_specialization` está
  contido nesse conjunto. Nenhuma conclusão além deste escopo exato deve ser
  extraída deste resultado.
- Conforme `AGENTS.md` (Seção 7), essa evidência permanece válida enquanto o
  código relevante não mudar e não houver dúvida material ou regressão que a
  invalide; se o código relevante mudar, os testes pertinentes devem ser
  reexecutados antes de qualquer nova declaração de conclusão.
- **PostgreSQL local:** observado, neste checkpoint, o serviço `db` do
  `docker-compose.yml` legado do projeto, mapeando porta do host `55432` para
  a porta `5432` do container, em estado `healthy` durante a execução dos
  testes desse conjunto de quatro arquivos que dependiam dele. Esta é uma
  **observação pontual de ambiente naquele momento**, não um estado permanente
  do ambiente local.
- **Atualização (checkpoint 2026-09-02):** durante a validação da frente
  `P-007`, uma regressão direcionada adicional (mesmos quatro arquivos)
  resultou em `108 passed, 0 failed`. Uma execução da suíte global completa
  (`pytest backend/tests`) resultou em `304 passed, 2 failed` de 306 testes
  coletados. As duas falhas
  (`test_admin_tenant_usage_full_returns_consolidated_view` e
  `test_rls_isolation`) foram diagnosticadas como externas à `P-007`. A
  prioridade do próximo ciclo (`P-002`, resolvida apenas como prioridade em
  `OPS-004`) é restaurar uma baseline confiável de testes e isolamento
  multi-tenant; a solução técnica dessas falhas dependia das decisões
  humanas A e B de `OPS-004`, tomadas em 2026-09-25 (A1 em `ARCH-001`, B2
  em `ARCH-002`) — direção decidida, **não implementada**. Este registro não
  reexecuta nem reconfirma esses resultados; é transcrição da evidência já
  obtida e registrada em `DECISIONS.md`.
- **Auditoria-mestra (2026-09-24):** nenhum teste foi executado. Observado
  no código: a suíte **não é hermética** (configuração carrega o `.env` da
  raiz do repositório; `test_rls_isolation` usa o PostgreSQL local real e
  grava dados); o CI possui 4 jobs e **não executa a suíte completa do
  backend**.
- **Atualização (checkpoint 2026-09-29 — BLOCO 1A):** a infraestrutura de
  testes backend foi tornada hermética no PR #311,
  `c75d2e6c9a503bb1db7b76a690097b355bab7fa2`, incluindo configuração de
  pytest, PostgreSQL de teste isolado, `conftest.py`, suporte específico a
  PostgreSQL e reconciliação dos testes envolvidos. Este checkpoint
  substitui, para o estado atual, a limitação de não hermeticidade observada
  em 2026-09-24; o registro histórico acima permanece preservado.
- **Atualização (checkpoint 2026-09-29 — BLOCO 2):** RLS PostgreSQL tenant
  real e versionado foi implementado no PR #312,
  `29f7bd45b729766417781a80d7dfff56ddb3aa49`, incluindo migration,
  integração de tenant/session, segurança e testes associados. Este
  checkpoint substitui, para o estado atual do código, a ausência de RLS
  versionado observada em 2026-09-24. Nenhuma afirmação sobre o estado ao
  vivo de Production decorre deste registro.
- **Atualização (checkpoint 2026-09-29 — BLOCO 1B):** a baseline completa do
  backend foi reexecutada em ambiente de teste isolado com PostgreSQL 16
  efêmero, resultando em `316 passed, 0 failed` (`112 warnings`). O PR #313,
  commit `5473a88656d49fac026f7e30856dca73557f202d`, adicionou o job
  `backend-full-suite` ao workflow de CI. No PR #313, os 5 checks executados
  ficaram verdes, incluindo `backend-full-suite`. Após essa comprovação,
  `backend-full-suite` foi adicionado aos status checks obrigatórios da
  proteção de `main`, preservando `smoke-backend`,
  `contract-saas-limits` e `strict: true`. Este registro substitui, para o
  estado atual, as limitações observadas pela auditoria de 2026-09-24 quanto
  à ausência da suíte completa no CI; o registro histórico acima permanece
  preservado. Nenhuma ação em Production foi realizada.

## E. Estado arquitetural/produto comprovado pela auditoria (nível: documentado por auditoria de leitura)

Resumo do que a auditoria de leitura (fase anterior a este checkpoint)
encontrou como implementado no código, sem ampliar para além do que foi
efetivamente lido:

- Backend FastAPI + SQLAlchemy + Alembic + PostgreSQL, com JWT, RBAC,
  segregação multi-tenant em nível de aplicação (`scoped_query`) e
  middleware de auditoria. **RLS PostgreSQL não está versionado:** a
  auditoria-mestra de 2026-09-24 não encontrou `ENABLE ROW LEVEL SECURITY`
  nem `CREATE POLICY` nas migrations; `set_config('app.tenant_id', ...)`
  existe em `backend/app/core/tenant.py`, mas nada versionado o consome.
  RLS consta como prometido/documentado, **não comprovado no Git**; o estado
  do banco local e de Production não foi verificado.
  **Atualização de 2026-09-29:** essa conclusão permanece como registro
  histórico da auditoria de 2026-09-24, mas foi superada para o estado
  corrente do código pelo BLOCO 2 de `OPS-005`: o PR #312
  (`29f7bd45b729766417781a80d7dfff56ddb3aa49`) implementou/versionou RLS
  PostgreSQL tenant com migration e testes associados. Esta atualização
  não comprova nem afirma o estado ao vivo de Production.
- Frontend React 19 + Vite 8.
- Módulo de copiloto de edição assistida concentrado em
  `backend/app/services/case_operational_assistant.py` (arquivo extenso,
  ~7.600 linhas na auditoria original — ver riscos na seção G).
- Módulos por domínio jurídico (`modules/engines`, `legal_editor`,
  `document_factory`, `parties_succession`, `appeals_reactions`, `jobs`) e
  registro de módulos jurídicos (`legal_modules`).
- Fluxo executivo (análise → resumo → relatório → PDF) presente no código,
  com testes associados na suíte do projeto.
- Billing com modelos `billing_request`/`subscription` e webhook de gateway
  de pagamento com verificação de token.

Esta seção descreve o que foi **encontrado no código** durante a auditoria de
leitura — não é, por si só, confirmação de que tudo está testado, validado ou
em produção (ver disciplina de certeza em `AGENTS.md`, Seção 8, e seção F
abaixo).

## F. Integrações e nível de certeza

Aplicando a disciplina de `AGENTS.md` (Seção 8) a cada integração observada na
auditoria:

- **OpenAI (LLM):** *implementado* e *integrado* no código
  (`services/llm_client.py`, provider `openai`); flag de ativação
  (`LLM_ANALYSIS_ENABLED`) observada com valor padrão desligado no código
  auditado. Não *verificado ao vivo* nesta sessão.
- **Asaas (pagamento):** *implementado* e *integrado* no código (checkout +
  webhook com verificação de token). Documentação histórica do projeto
  (handoff datado) **afirma** configuração de produção — isso é classificado
  aqui apenas como **"documentado como produção"**, não como "verificado ao
  vivo em produção" nem "autorizado para produção" por este checkpoint, pois
  nenhuma verificação ao vivo em Production foi realizada nesta sessão.
- **Hospedagem (Railway, citada em documentação histórica):** mesma
  classificação — **"documentado como produção"** apenas, sem verificação ao
  vivo por este checkpoint.
- **WhatsApp:** não há integração de API ativa encontrada no código auditado;
  existe apenas um campo de metadado (`contact_type`) para registro manual de
  contato.

## G. Riscos e lacunas relevantes (herdados da auditoria, sem ampliação)

- Arquivo monolítico `case_operational_assistant.py` (maior arquivo de longe
  do backend na auditoria original) — risco de manutenção e de regressão
  silenciosa, sem decisão humana registrada sobre refatoração.
- Documentação do projeto historicamente fragmentada entre dezenas de
  arquivos em `docs/`, sem índice único até este checkpoint.
- Itens de release/gate e de política LGPD que os próprios documentos do
  projeto (`RELEASE_CHECKLIST_MVP.md`, `docs/LGPD_MINIMA.md`) descrevem como
  parciais ou pendentes, conforme observado na auditoria.
- Existência de múltiplos arquivos `.env.bak*` na raiz do repositório de
  produto — tratado como **risco de higiene/segurança a verificar
  futuramente**, sem que este checkpoint tenha lido ou exposto qualquer
  conteúdo desses arquivos.
- **Achados da auditoria-mestra (2026-09-24), somente leitura:**
  - RLS prometido/documentado, mas não versionado (ver Seção E).
  - Suíte completa do backend fora do CI; testes não herméticos (Seção D).
  - **Atualização de 2026-09-29:** os dois achados anteriores sobre RLS e
    infraestrutura de testes/CI permanecem como histórico da auditoria de
    2026-09-24, mas foram superados pelos BLOCOs 1A, 2 e 1B de `OPS-005`
    (PRs #311, #312 e #313). Os demais achados desta lista não são
    declarados resolvidos por essa sequência.
  - Nenhum rate limiting encontrado no HEAD auditado.
  - Dump local de banco (`ia_trabalhista_before_case_cleanup_2026-04-14.dump`)
    e arquivos em `backend/storage` presentes localmente — exigem decisão
    e higiene LGPD (relacionado a `P-005`/`P-009`); conteúdo não aberto.
  - Production **NÃO VERIFICADA**.
  - 14 branches locais não mescladas em `main` — exigem auditoria futura;
    nenhuma foi alterada.
- **Achado da investigação da semântica do limite administrativo
  (2026-09-25), somente leitura — registrado em `ARCH-002`, sem solução
  decidida:** `cases_per_month` é alias legado de `active_cases_limit`,
  mas `remaining.cases` é calculado contra o contador mensal
  `cases_created`, misturando limite de casos **ATIVOS** com casos
  **CRIADOS NO MÊS**. Por `OPS-005`, fica **congelado** na frente
  1A → 2 → 1B e exige decisão humana própria futura antes de qualquer
  mudança de contrato.

## H. Estado da implantação dos 7 arquivos de governança

**Checkpoint 2026-09-01 (histórico):** os 7 arquivos foram materializados e
validados no worktree de governança, untracked, não staged, não
commitados.

**Checkpoint 2026-09-02 (histórico pós-integração):** os 7 arquivos foram commitados
(`chore/governance-docs-v1`, `f52fece9ce2e13204f707b54ee0ff26e73ac5b43`),
integrados a `main` via PR #305 (squash-merged), e posteriormente o
código/produto de `P-007` (PR #306) e o fechamento documental de `P-007` em
`DECISIONS.md` (PR #307) também foram integrados a `main`. `main` local e
`origin/main` estão sincronizadas em
`0fc0755d7de4ced50400f6e297a99338f6d9cd50`. O worktree de governança
temporário
(`/home/dilsondev/projetos/ia_trabalhista_robusta-governance-docs-v1`) e a
branch `docs/close-p007-decision-v1` foram removidos após comprovação de
equivalência material de conteúdo. A branch `chore/governance-docs-v1` não
foi removida (permanece como registro histórico do commit
`f52fece9ce2e13204f707b54ee0ff26e73ac5b43`, sem worktree associado).

Estes valores refletem o observado neste checkpoint; o estado real do Git
deve ser reverificado diretamente em cada nova sessão (Seção B) — este
registro não o substitui.

## I. Decisões humanas pendentes

As decisões humanas pendentes estão formalizadas em `DECISIONS.md`. Neste
checkpoint, `P-001`, `P-003` a `P-006` e `P-008` a `P-010` permanecem
pendentes; `P-007` foi resolvida (`OPS-003`) e `P-002` foi resolvida
**apenas como prioridade** (`OPS-004`); as decisões técnicas A e B de
`OPS-004` foram tomadas por humano em 2026-09-25 (A1 em `ARCH-001`, B2 em
`ARCH-002`). A sequência técnica subsequente `OPS-005`
(BLOCO 1A → BLOCO 2 → BLOCO 1B) foi concluída pelos PRs #311, #312 e #313.
`PROJECT_STATE.md` não resolve, renumera nem substitui essas decisões; para o estado normativo corrente e completo, consultar
diretamente `DECISIONS.md`.

Síntese temática (apenas resumo — `DECISIONS.md` é a fonte normativa):

- Nomenclatura oficial do produto. (`P-001`, pendente)
- Prioridade do próximo ciclo de desenvolvimento. (`P-002`, resolvida em
  `OPS-004` apenas como prioridade: baseline confiável de testes e
  isolamento multi-tenant antes de novas features; decisões A — modelo de
  isolamento — e B — semântica do limite admin — tomadas em 2026-09-25:
  A1 (`ARCH-001`) e B2 (`ARCH-002`); sequência técnica `OPS-005`
  posteriormente concluída nos PRs #311, #312 e #313; a semântica de
  `remaining.cases`/`cases_per_month` permanece fora desse fechamento e
  dependente de decisão humana futura)
- Eventual refatoração de `case_operational_assistant.py`. (`P-003`,
  pendente)
- Fechamento formal do gate de release. (`P-004`, pendente)
- Política formal de retenção/descarte de dados (LGPD). (`P-005`,
  pendente)
- Nível de autonomia de agentes de IA neste projeto. (`P-006`, pendente)
- Destino/fechamento da frente local
  `fix/editor-civil-professional-risk-specialization-v1`. (`P-007`,
  resolvida em `OPS-003`)
- Higiene de `.env`/`.env.bak*` na raiz do repositório de produto.
  (`P-008`, pendente)
- Eventual adoção de storage externo para anexos. (`P-009`, pendente)
- Necessidade/prioridade de auditoria técnica aprofundada de áreas ainda
  não auditadas em detalhe. (`P-010`, pendente)

## J. Limites do que este checkpoint NÃO comprova

- Não comprova que o produto está "totalmente validado" — apenas que uma
  regressão direcionada, com o escopo descrito na seção D, foi informada como
  executada antes desta implantação de governança.
- Não comprova, nem afirma, nenhum estado ao vivo de Production — nenhuma
  verificação ao vivo em Production foi realizada nesta sessão.
- Não substitui a necessidade de qualquer sessão futura consultar o Git
  diretamente para saber a branch, o HEAD, `origin/main` ou o estado do
  working tree correntes.
- Não decide nenhuma das pendências humanas listadas na seção I; apenas
  espelha decisões humanas registradas em `DECISIONS.md`.
- Não define automaticamente qual será o próximo trabalho técnico do produto.
  A tarefa operacional corrente deve ser consultada em `NEXT_STEP.md`, cuja
  existência não constitui, por si só, autorização automática de execução,
  conforme `AGENTS.md` e `DECISIONS.md`.
- Não expõe, e nunca expôs nesta sessão, conteúdo de `.env`, `.env.bak*` ou
  qualquer segredo.
