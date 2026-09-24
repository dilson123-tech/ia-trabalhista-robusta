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

- **Último checkpoint Git observado (2026-09-24):** `main` local e
  `origin/main` (referência local, sem `fetch`) em
  `0fc0755d7de4ced50400f6e297a99338f6d9cd50`; branch documental
  `docs/resolve-p002-governance-v1` criada a partir desse hash, com
  alterações locais não commitadas nos 4 documentos desta reconciliação.
- **Estado geral estimado — ESTIMATIVAS qualitativas da auditoria-mestra,
  NÃO métricas formais:**

  | Área | Estimativa |
  |---|---|
  | Geral | ~65% |
  | Governança | ~80% |
  | Backend | ~80% |
  | Frontend | ~60% |
  | Banco/RLS | ~40% |
  | Segurança | ~55% |
  | IA jurídica | ~65% |
  | Billing | ~60% |
  | LGPD | ~35% |
  | Testes/CI | ~50% |
  | Release | ~40% |
  | Production | **NÃO VERIFICADA** |

- **Pronto (implementado no código, conforme auditoria de leitura):**
  backend FastAPI `/api/v1` com JWT, RBAC, isolamento multi-tenant em nível
  de aplicação (`scoped_query`) e auditoria; motores jurídicos, editor e
  fluxo executivo com testes associados; billing com checkout/webhook
  Asaas no código; frontend React com os principais fluxos; governança
  persistente (7 arquivos) em `main`.
- **Faltando:** RLS PostgreSQL versionado (ou decisão formal por isolamento
  somente em aplicação); suíte hermética e suíte completa em CI; rate
  limiting; políticas LGPD formais (retenção/descarte); painéis de frontend
  ainda só visuais (Recursos e Sucessão); gate de release formal.
- **Bloqueios:** decisões humanas A (modelo de isolamento) e B (semântica
  do limite admin) pendentes em `OPS-004`; as 2 falhas conhecidas da suíte
  global sem solução técnica decidida.
- **Último resultado de testes conhecido:** suíte global `304 passed,
  2 failed` em 306 testes; regressão direcionada `108 passed, 0 failed`
  (ambos registrados em `OPS-003`/Seção D; **não reexecutados** na
  auditoria-mestra).
- **Próximo passo:** fechar esta atualização documental (BLOCO 0) →
  DICO/ChatGPT decidem A e B → somente então, com nova autorização
  específica, BLOCO 1 (ver `NEXT_STEP.md`).
- **Decisões humanas abertas:** A e B (`OPS-004`); `P-001`, `P-003`,
  `P-004`, `P-005`, `P-006`, `P-008`, `P-009`, `P-010`.

## B. Git / baseline observado (neste checkpoint, não permanente)

- **Repositório de produto original:** `/home/dilsondev/projetos/ia_trabalhista_robusta`
- **Branch de trabalho original observada:** `fix/editor-civil-professional-risk-specialization-v1`
- **Baseline Git observado/aprovado:** `4e9d22fdae99fc717192ea5b6b96214f61d70628`
- **`origin/main` observado neste checkpoint:** mesmo hash,
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
  multi-tenant; a solução técnica dessas falhas **não está decidida** e
  depende das decisões humanas A e B de `OPS-004`. Este registro não
  reexecuta nem reconfirma esses resultados; é transcrição da evidência já
  obtida e registrada em `DECISIONS.md`.
- **Auditoria-mestra (2026-09-24):** nenhum teste foi executado. Observado
  no código: a suíte **não é hermética** (configuração carrega o `.env` da
  raiz do repositório; `test_rls_isolation` usa o PostgreSQL local real e
  grava dados); o CI possui 4 jobs e **não executa a suíte completa do
  backend**.

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
  - Nenhum rate limiting encontrado no HEAD auditado.
  - Dump local de banco (`ia_trabalhista_before_case_cleanup_2026-04-14.dump`)
    e arquivos em `backend/storage` presentes localmente — exigem decisão
    e higiene LGPD (relacionado a `P-005`/`P-009`); conteúdo não aberto.
  - Production **NÃO VERIFICADA**.
  - 14 branches locais não mescladas em `main` — exigem auditoria futura;
    nenhuma foi alterada.

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
**apenas como prioridade** (`OPS-004`), com as decisões técnicas A e B de
`OPS-004` pendentes (humanas). `PROJECT_STATE.md` não resolve, renumera nem substitui
essas decisões; para o estado normativo corrente e completo, consultar
diretamente `DECISIONS.md`.

Síntese temática (apenas resumo — `DECISIONS.md` é a fonte normativa):

- Nomenclatura oficial do produto. (`P-001`, pendente)
- Prioridade do próximo ciclo de desenvolvimento. (`P-002`, resolvida em
  `OPS-004` apenas como prioridade: baseline confiável de testes e
  isolamento multi-tenant antes de novas features; decisões A — modelo de
  isolamento — e B — semântica do limite admin — pendentes; nenhuma branch
  técnica criada ou autorizada)
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
- Não decide nenhuma das pendências humanas listadas na seção I.
- Não define automaticamente qual será o próximo trabalho técnico do produto.
  A tarefa operacional corrente deve ser consultada em `NEXT_STEP.md`, cuja
  existência não constitui, por si só, autorização automática de execução,
  conforme `AGENTS.md` e `DECISIONS.md`.
- Não expõe, e nunca expôs nesta sessão, conteúdo de `.env`, `.env.bak*` ou
  qualquer segredo.
