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
- Este checkpoint só deve ser atualizado quando houver mudança material de
  estado, houver evidência objetiva, rastreável e válida para o estado relevante
  do código — inclusive evidência de checkpoint anterior quando continuar válida
  pelos critérios de `AGENTS.md` Seção 7 —, a atualização fizer parte de tarefa
  autorizada e forem respeitadas as regras de aprovação de `AGENTS.md`. Memória
  de agente ou afirmação de conversa nunca substitui evidência.

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

## C. Frente local aberta (preservada, não commitada)

A branch `fix/editor-civil-professional-risk-specialization-v1` possui, neste
checkpoint, trabalho local **não commitado** em dois arquivos:

- `backend/app/services/case_operational_assistant.py`
- `backend/tests/test_massive_multicase_all_blocks_regression.py`

Esses dois arquivos foram verificados byte a byte, via SHA-256, imediatamente
após a criação do worktree de governança, para comprovar que permaneceram
intocados:

```
c03c633727fd0510727b54816b56fdba8a2ff22ae6e183db81cc90bb5b519013  backend/app/services/case_operational_assistant.py
5bb2ae19ee222b90cb56958a3d0afff47b89ab387ba96b902878e09f52b42103  backend/tests/test_massive_multicase_all_blocks_regression.py
```

**A governança está sendo implantada em um worktree separado precisamente para
não misturar essa frente local com o rollout dos arquivos de governança.** O
destino final dessa frente (quando/como commitar, abrir PR, ou outra decisão)
permanece uma decisão humana pendente, formalizada em `DECISIONS.md` como
`P-007`. Este `PROJECT_STATE.md` apenas registra o estado observado e não
resolve nem antecipa a decisão.

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

## E. Estado arquitetural/produto comprovado pela auditoria (nível: documentado por auditoria de leitura)

Resumo do que a auditoria de leitura (fase anterior a este checkpoint)
encontrou como implementado no código, sem ampliar para além do que foi
efetivamente lido:

- Backend FastAPI + SQLAlchemy + Alembic + PostgreSQL, com JWT, RBAC,
  segregação multi-tenant (incluindo RLS em Postgres) e middleware de
  auditoria.
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

## H. Estado da implantação dos 7 arquivos de governança (neste checkpoint)

| Arquivo | Estado |
|---|---|
| `AGENTS.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |
| `PROJECT_STATE.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |
| `ROADMAP.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |
| `ARCHITECTURE.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |
| `DECISIONS.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |
| `NEXT_STEP.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |
| `CLAUDE.md` | Criado e validado no worktree de governança. Untracked, não staged, não commitado, sem push, sem PR. |

**7 de 7 arquivos materializados e validados neste checkpoint.** Isso
**não** significa commitados, integrados em `main`, publicados, Production
verificada, ou produto totalmente validado — nenhuma dessas afirmações é
feita por este registro.

**Isolamento da implantação:**

- Worktree de governança: `/home/dilsondev/projetos/ia_trabalhista_robusta-governance-docs-v1`
- Branch de governança: `chore/governance-docs-v1`
- Este worktree nasceu limpo, exatamente no baseline aprovado
  `4e9d22fdae99fc717192ea5b6b96214f61d70628`, verificado por leitura
  (`git rev-parse HEAD` no worktree novo == hash aprovado; `git status
  --porcelain` vazio no momento da criação).
- O repositório principal, na branch
  `fix/editor-civil-professional-risk-specialization-v1`, foi verificado
  por leitura como intocado após a criação de cada um dos 7 arquivos —
  mesma branch, mesmos dois arquivos modificados, mesmos hashes SHA-256 da
  Seção C, confirmados em todas as verificações realizadas.
- Estes valores refletem o observado neste checkpoint; o estado real do
  Git deve ser reverificado diretamente em cada nova sessão (Seção B) —
  este registro não o substitui.

## I. Decisões humanas pendentes

As decisões humanas pendentes estão formalizadas em `DECISIONS.md`. Neste
checkpoint, `P-001` a `P-010` permanecem registradas conforme seu estado
naquele documento. `PROJECT_STATE.md` não resolve, renumera nem substitui
essas decisões; para o estado normativo corrente, consultar diretamente
`DECISIONS.md`.

Síntese temática (apenas resumo — `DECISIONS.md` é a fonte normativa):

- Nomenclatura oficial do produto.
- Prioridade do próximo ciclo de desenvolvimento.
- Eventual refatoração de `case_operational_assistant.py`.
- Fechamento formal do gate de release.
- Política formal de retenção/descarte de dados (LGPD).
- Nível de autonomia de agentes de IA neste projeto.
- Destino/fechamento da frente local atual
  (`fix/editor-civil-professional-risk-specialization-v1`).
- Higiene de `.env`/`.env.bak*` na raiz do repositório de produto.

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
