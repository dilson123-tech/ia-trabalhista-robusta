# ROADMAP.md — Planejamento (não é autorização de execução)

## A. Finalidade e regras de leitura

Este documento consolida o planejamento disperso hoje em `docs/ROADMAP.md`,
`docs/PILOT_BACKLOG.md`, `docs/OPERATIONAL_PIPELINE_CHECKPOINT_V1.md`,
`MVP_VALIDATION_MATRIX.md` e `RELEASE_CHECKLIST_MVP.md`, além do que a
auditoria de governança e `PROJECT_STATE.md` já registraram.

Regras de leitura obrigatórias, herdadas de `AGENTS.md`:

- **`ROADMAP.md` é planejamento — não é autorização automática de execução**
  (`AGENTS.md`, Seção 5). Nenhuma frente aqui listada pode ser iniciada apenas
  porque está escrita aqui.
- **Concluir uma etapa não autoriza, por si só, iniciar automaticamente a
  seguinte.** Início de trabalho técnico exige tarefa compatível com
  `NEXT_STEP.md` e autorização humana quando exigida por
  `AGENTS.md`/`DECISIONS.md`.
- Marcadores `✅` indicam **comprovação no escopo declarado da fonte citada** —
  nunca "produto pronto" de forma genérica. Ver disciplina de certeza em
  `AGENTS.md`, Seção 8 (implementado / integrado / testado / validado /
  documentado como produção / verificado ao vivo em produção / autorizado
  para produção).
- Nenhuma decisão humana pendente é resolvida por este documento. As
  pendências são resumidas na Seção L e formalizadas com IDs `P-*` em
  `DECISIONS.md`, que é a fonte normativa para seu estado.
- Percentuais neste documento são **estimativas operacionais qualitativas**,
  não medições automatizadas — cada uma indica o critério usado.

## B. Visão do produto

Segundo `README.md` e `docs/PRODUTO_OFICIAL.md`: SaaS jurídico com núcleo
trabalhista, arquitetura pensada para evolução modular multiárea (cível,
criminal, família, previdenciário, consumidor). A nomenclatura oficial
("IA Trabalhista Robusta" vs. "Plataforma Jurídica Pro") é decisão humana
pendente, já registrada em `AGENTS.md`/`PROJECT_STATE.md` — este roadmap não a
antecipa.

## C. Fases/frentes já implementadas ou avançadas

- ✅ Autenticação JWT, RBAC e isolamento multi-tenant **em nível de
  aplicação** (`scoped_query`) — implementado e testado, per
  `MVP_VALIDATION_MATRIX.md` (itens `[x]` nas seções 2 e 3) e suíte de testes
  (`test_tenant_isolation.py`, `test_multi_tenant_isolation.py`).
- ⚠️ **RLS PostgreSQL — NÃO comprovado no Git:** documentado/prometido, mas a
  auditoria-mestra de 2026-09-24 não encontrou `ENABLE ROW LEVEL SECURITY`
  nem `CREATE POLICY` nas migrations versionadas; `set_config('app.tenant_id',
  ...)` existe no código, mas nada versionado o consome. `test_rls_isolation`
  é um dos 2 testes com falha conhecida, depende do PostgreSQL local real e
  não é hermético. O modelo de isolamento foi decidido por humano em
  2026-09-25 — **A1** (`ARCH-001`): RLS PostgreSQL real e versionado,
  mantendo `scoped_query` como camada adicional (policies por migration,
  role de aplicação não superusuária e sem `BYPASSRLS`, tratamento explícito
  de ownership/`FORCE ROW LEVEL SECURITY`, teste em PostgreSQL real e CI).
  **Não implementado.**
- ✅ Fluxo executivo caso → análise → resumo → relatório → PDF — implementado
  e testado, per `MVP_VALIDATION_MATRIX.md` (seções 4–6) e serviços auditados
  (`decision_engine.py`, `report_engine.py`, `pdf_executive.py`).
- ✅ Health/CI/smoke — implementado e testado, per
  `.github/workflows/ci.yml` e seção 1 da matriz. Limites observados na
  auditoria-mestra (2026-09-24): apenas o endpoint `/health` foi encontrado
  (sem `/ready`); o CI possui 4 jobs e **não executa a suíte completa do
  backend**.
- ✅ Cobertura extensa de especialização trabalhista e consumidor no editor
  assistido — implementado, com cadeia de PRs mesclados (#284–#299) e testes
  correspondentes (`test_editor_labor_template_routing.py` e a família
  `test_editor_civil_*`/consumidor).
- ✅ Billing técnico (checkout + webhook Asaas com verificação de token) —
  implementado e integrado no código (`payment_checkout.py`, `webhooks.py`);
  ver Seção I para o limite exato dessa comprovação.
- ✅ **Governança documental persistente de IA** — 7/7 arquivos criados,
  commitados e integrados em `main` (PR #305, squash-merged). Registra a
  conclusão da implantação documental; não resolve, por si só, pendências
  de produto.
- ✅ **Especialização cível — restrição/risco profissional (LGPD)**: frente
  commitada (`7771de0384d9c9bd56f6ecb62f855674a3d96ed6`), integrada a
  `main` via PR #306 (squash-merged,
  `b9ca8a8141da1a582a0ee2842b9278652e1705f4`). `P-007` resolvida em
  `DECISIONS.md`, `OPS-003` — ver detalhes completos lá.

## D. Frentes em andamento

- 🔄 **Módulo Criminal V1**: escopo oficial definido
  (`docs/CRIMINAL_MODULE_V1_SCOPE.md`), com roteamento parcial já no código
  (`test_editor_criminal_template_routing.py`). O próprio escopo declara que
  fluxos completos (júri, recursos avançados) estão fora do V1.

## E. Frentes pendentes

- ⏳ Refino do relatório/PDF para "padrão premium" (README, "Próximos focos").
- ⏳ Documentação operacional completa de produção — marcada `[~]` em
  `RELEASE_CHECKLIST_MVP.md`.
- ⏳ Decisão entre as 4 opções listadas em
  `docs/OPERATIONAL_PIPELINE_CHECKPOINT_V1.md` (integração Checklist+WhatsApp,
  refino visual, documentação comercial da esteira, exportação futura do
  dossiê interno) — nenhuma priorizada.
- ⚠️⏳ **Refatoração de `case_operational_assistant.py`**: identificada como
  risco arquitetural na auditoria, mas **não é tarefa automática deste
  roadmap** — depende de decisão humana ainda pendente.
- ✅ **Prioridade técnica de `P-002` / sequência `OPS-005`: concluída.**
  As decisões A1 (`ARCH-001`) e B2 (`ARCH-002`) foram executadas dentro da
  sequência obrigatória BLOCO 1A → BLOCO 2 → BLOCO 1B:
  - **BLOCO 1A:** concluído no PR #311
    (`c75d2e6c9a503bb1db7b76a690097b355bab7fa2`) — infraestrutura de testes
    backend hermética e PostgreSQL de teste isolado;
  - **BLOCO 2:** concluído no PR #312
    (`29f7bd45b729766417781a80d7dfff56ddb3aa49`) — RLS PostgreSQL tenant real
    e versionado, com migration e testes associados;
  - **BLOCO 1B:** concluído no PR #313
    (`1e7a686c602621ab5eaa86fdc9aaf3edd99e7833`) — suíte backend completa no
    CI, `backend-full-suite` obrigatório e baseline final registrada em
    `316 passed, 0 failed`, `112 warnings`.
- ⏳ **Defeito de contrato fora do fechamento de `OPS-005`:**
  `remaining.cases` é calculado contra `cases_created`, enquanto
  `cases_per_month` é alias legado de `active_cases_limit`. Sua semântica
  permanece **congelada** e exige decisão humana própria futura.
- ⏳ As frentes posteriores já existentes no planejamento — segurança/LGPD,
  billing/Asaas, frontend faltante e gate de release — permanecem sujeitas
  à sua própria evidência, auditoria/proposta e autorização humana. A
  conclusão de `OPS-005` **não autoriza automaticamente** nenhuma delas.
- 🚫 Production permanece **NÃO VERIFICADA** neste checkpoint; PostgreSQL 16
  usado nos testes não afirma a versão de Production.

## F. Segurança/LGPD

- ✅ LGPD mínima documentada (`docs/LGPD_MINIMA.md`), com controles descritos
  para autenticação, minimização de exposição, logs, relatórios/PDFs — dentro
  do escopo que o próprio documento declara como "LGPD mínima do MVP vendável",
  não conformidade total.
- ⏳⚠️ Política formal de retenção/descarte de dados — o próprio
  `docs/LGPD_MINIMA.md` a lista como pendência aberta; permanece pendência até
  decisão/evidência adequada (regra 9).
- ⏳⚠️ Fluxo formal externo de atendimento a direitos do titular — mesma
  situação, pendência auto-declarada.
- ⚠️ Existência de `.env`/`.env.bak*` na raiz do repositório de produto —
  risco de higiene a verificar, sem leitura de conteúdo nesta auditoria nem
  neste roadmap.
- ✅ Regra permanente de nunca expor segredos — fixada em `AGENTS.md`, Seção 6.
- ⚠️ Nenhum rate limiting encontrado no HEAD auditado (auditoria-mestra,
  2026-09-24).
- ⚠️ Dump local de banco e arquivos em `backend/storage` presentes no
  ambiente local — exigem decisão e higiene LGPD (conteúdo não aberto).

## G. Confiabilidade jurídica

- ✅ Princípio de não inventar fatos/provas/valores/jurisprudência —
  observado tanto na documentação (`docs/PROJECT_RULES.md`,
  `docs/CRIMINAL_MODULE_V1_SCOPE.md`) quanto no padrão de texto gerado pelo
  código auditado (blocos de especialização revisados nesta sessão instruem
  explicitamente a não presumir fatos não confirmados).
- ✅ Revisão profissional do advogado como exigência **documentada** em
  múltiplas fontes (`docs/PRODUTO_OFICIAL.md`, `docs/CRIMINAL_MODULE_V1_SCOPE.md`,
  `AGENTS.md` Seção 2) — esta é uma política de produto e de processo
  documentada e consistente com o código revisado; **não é**, por si só,
  verificação ao vivo de que todo protocolo real passou por essa revisão.
- ✅ Distinção fato confirmado / inferência / hipótese / pendência — praticada
  nos textos gerados observados na auditoria inicial de governança e no diff
  local revisado da frente de especialização cível
  (`case_operational_assistant.py`, ramo
  `civil_professional_risk_restriction_claim`). `PROJECT_STATE.md` (Seção C)
  registra a existência e preservação dessa frente como checkpoint, mas não é
  a fonte da análise textual em si.

## H. Arquitetura/manutenibilidade

- 🚨⚠️ `case_operational_assistant.py`: maior arquivo do backend, de longe,
  na auditoria original (~7.600 linhas) — risco de manutenção e regressão
  silenciosa. Registrado como risco, não como tarefa agendada.
- ✅ `ARCHITECTURE.md` criado e validado no worktree de governança — mapa da
  arquitetura comprovada/documentada do sistema, sujeito aos limites
  declarados no próprio documento.
- ✅ Padrão modular por domínio jurídico (`modules/engines`, `legal_editor`,
  `document_factory`, `parties_succession`, `appeals_reactions`, `jobs`) —
  implementado como estrutura extensível, coerente com a diretriz permanente
  do README de "núcleo genérico + regras por domínio".
- ⏳ Documentação histórica fragmentada entre 50+ arquivos em `docs/`, sem
  índice único até a criação desta governança.

## I. Billing/comercialização

- ✅ Implementado/integrado/testado **no nível de código**: modelos
  `billing_request`/`subscription`, checkout com provider configurável,
  webhook Asaas com verificação HMAC de token.
- 📄 **Documentado como produção**: `docs/HANDOFF_FINAL_PRODUCAO_2026-04-28.md`
  afirma Asaas de produção configurado, webhook ativo, e um pagamento Pix real
  confirmado. Esta é uma afirmação de documento histórico — **não verificada
  ao vivo em produção nesta sessão nem por este roadmap** (🚫 fora do escopo
  autorizado desta etapa).
- ⏳ Material comercial (`docs/COMMERCIAL_PLANS_MVP.md`,
  `docs/TABELA_COMERCIAL_INICIAL.md`, etc.) existe como documentação; seu
  estado comercial ativo não foi reverificado nesta auditoria.

## J. Release/produção

- 🔄 `RELEASE_CHECKLIST_MVP.md`: maioria dos itens técnicos marcados `[x]`,
  mas o próprio "gate de release" (seção 9 da matriz/checklist) mantém itens
  `[ ]` em aberto: "todos os fluxos críticos validados", "todos os cenários
  críticos de erro validados", "sem falhas abertas graves".
- ⚠️ **Fechamento formal do gate de release é decisão humana pendente** —
  este roadmap não o declara fechado.
- 📄 Estado de produção descrito em documentação histórica (`HANDOFF_FINAL...`)
  — classificado apenas como "documentado como produção"; **verificação ao
  vivo em Production não foi realizada e não está autorizada nesta etapa**
  (🚫).

## K. Governança de IA

- ✅ `AGENTS.md` — criado e validado no worktree de governança; não
  staged/commitado.
- ✅ `PROJECT_STATE.md` — criado e validado no worktree de governança; não
  staged/commitado.
- ✅ `ROADMAP.md` — criado e validado no worktree de governança; não
  staged/commitado.
- ✅ `ARCHITECTURE.md` — criado e validado no worktree de governança; não
  staged/commitado.
- ✅ `DECISIONS.md` — criado e validado no worktree de governança; não
  staged/commitado.
- ✅ `NEXT_STEP.md` — criado e validado no worktree de governança; não
  staged/commitado.
- ✅ `CLAUDE.md` — criado e validado no worktree de governança; não
  staged/commitado.

**Governança documental inicial: 7 de 7 arquivos materializados e
validados neste checkpoint.** Nenhum staged, commitado, enviado por push
ou com PR aberto. **Implantação MATERIAL concluída** — isso, por si só, não
alterou prioridades técnicas. *(Registro histórico do checkpoint de
implantação; posteriormente os 7 arquivos foram integrados a `main` via
PR #305 — ver Seção C; `P-007` foi resolvida em `OPS-003` e `P-002` apenas
como prioridade em `OPS-004`.)*

## L. Decisões humanas que bloqueiam ou condicionam fases

As decisões abaixo estão formalizadas com IDs `P-*` em `DECISIONS.md`, que é
a fonte normativa. Esta seção apenas resume o que cada pendência bloqueia ou
condiciona neste roadmap; não resolve nenhuma delas.

- **Nomenclatura oficial do produto — `P-001`** — condiciona comunicação
  externa e comercial consistente (Seção B).
- **Prioridade do próximo ciclo de desenvolvimento — `P-002`** — resolvida
  em `OPS-004` como prioridade: estabelecer baseline confiável de testes e
  isolamento multi-tenant antes de novas features. As decisões humanas A1
  (`ARCH-001`) e B2 (`ARCH-002`) foram tomadas em 2026-09-25, e o modelo de
  execução obrigatório 1A → 2 → 1B foi definido em `OPS-005`. Essa sequência
  foi posteriormente concluída e integrada a `main` pelos PRs #311, #312 e
  #313, respectivamente. O defeito de contrato de `remaining.cases` /
  `cases_per_month` permaneceu fora desse fechamento, com semântica congelada
  até decisão humana própria futura (Seção E).
- **Refatoração de `case_operational_assistant.py` — `P-003`** — condiciona
  a evolução segura da Seção H; não deve ser tratada como tarefa automática
  deste roadmap.
- **Fechamento formal do gate de release — `P-004`** — bloqueia qualquer
  declaração ampliada de "pronto para mercado" além do que já está
  evidenciado (Seção J).
- **Política formal de retenção/descarte de dados (LGPD) — `P-005`** —
  bloqueia fechamento formal de conformidade mínima permanente (Seção F).
- **Nível de autonomia dos agentes de IA — `P-006`** — condiciona quanto
  `NEXT_STEP.md` poderá ser executado sem aprovação humana passo a passo.
- **Destino/fechamento da frente local — `P-007`** — resolvida em
  `OPS-003`: a frente foi commitada, integrada a `main` via PR #306
  (squash-merged) e a branch de trabalho foi removida após comprovação de
  equivalência material de conteúdo (Seção C).
- **Higiene de `.env`/`.env.bak*` — `P-008`** — condiciona o fechamento de
  segurança operacional (Seção F).
- **Storage externo para anexos — `P-009`** e **auditoria técnica
  aprofundada — `P-010`** — pendentes em `DECISIONS.md`; não resolvidas por
  este roadmap.

## M. Critérios de passagem entre fases

- **⏳ → 🔄**: exige compatibilidade com `NEXT_STEP.md` e as
  autorizações aplicáveis conforme `AGENTS.md` e `DECISIONS.md`; enquanto o
  nível de autonomia dos agentes permanecer decisão humana pendente, não
  ampliar autonomia por inferência. Nunca ocorre apenas por estar listado
  neste roadmap — `ROADMAP.md` sozinho nunca autoriza execução.
- **🔄 → ✅**: exige evidência objetiva e rastreável (testes reexecutados
  quando o código mudou, revisão humana do resultado), registrada no
  checkpoint apropriado (`PROJECT_STATE.md` ou equivalente) — nunca por
  afirmação de conversa ou memória de agente (`AGENTS.md`, Seção 7).
- **✅ de uma frente não propaga automaticamente ✅ para outra** — cada frente
  é avaliada por sua própria evidência declarada.
- Qualquer conflito entre este roadmap e o estado real do código/Git segue a
  regra de `AGENTS.md`, Seção 4: parar, relatar, aguardar orientação humana.

## N. Árvore de progresso (estimativas qualitativas, não medição automatizada)

*Critério das estimativas abaixo: proporção observada de itens marcados `[x]`
versus total de itens na fonte citada, ou densidade de evidência de código
encontrada na auditoria — não é métrica automatizada nem projeção temporal.*

```
IA Trabalhista Robusta / [nomenclatura oficial pendente]
│
├── 🔄 Infra base (auth, tenant app-level, health, CI, plans/limits)
│     OPS-005 concluída: infraestrutura de testes backend hermética no
│     PR #311; RLS PostgreSQL tenant real/versionado no PR #312; suíte
│     backend completa no CI e `backend-full-suite` obrigatório no PR #313.
│     Baseline final registrada: 316 passed, 0 failed, 112 warnings.
│     Os percentuais antigos de Banco/RLS, Testes/CI e Segurança eram
│     estimativas da auditoria de 2026-09-24 e não foram recalculados.
│     /ready, rate limiting e demais itens fora de OPS-005 não são
│     declarados resolvidos por esta reconciliação.
│
├── ✅ Fluxo executivo (análise → resumo → relatório → PDF)
│     estimativa: ~85% — quase todos os itens [x] na seção 6 da matriz
│
├── 🔄 Motor de especialização jurídica (copiloto/editor)
│     estimativa: ~65% — cobertura extensa trabalhista/consumidor; cível
│     ampliada (especialização de risco profissional integrada via PR #306,
│     P-007 resolvida em OPS-003); criminal V1 parcial
│
├── 🔄 Billing/Asaas
│     estimativa: ~70% no código (implementado/integrado/testado);
│     produção "documentada", não verificada ao vivo por este roadmap
│
├── ✅ Governança documental de IA
│     progresso documental: 7 de 7 arquivos materializados e validados
│     (AGENTS.md, PROJECT_STATE.md, ROADMAP.md, ARCHITECTURE.md,
│     DECISIONS.md, NEXT_STEP.md, CLAUDE.md). Implantação MATERIAL
│     concluída e posteriormente integrada a main via PR #305.
│     Este número mede apenas o progresso da implantação documental da
│     governança — não percentual de conclusão técnica do produto.
│     P-007 resolvida (OPS-003); P-002 definiu a prioridade em OPS-004;
│     A1 (ARCH-001) / B2 (ARCH-002) foram executadas dentro da sequência
│     1A → 2 → 1B de OPS-005, concluída pelos PRs #311, #312 e #313.
│
├── ⏳ LGPD formal (retenção/descarte/exportação/exclusão)
│     auto-declarado parcial pelo próprio docs/LGPD_MINIMA.md
│
├── ⏳ Release gate final
│     itens [ ] explícitos em RELEASE_CHECKLIST_MVP.md, sem fechamento humano
│
├── ⚠️⏳ Refatoração do arquivo monolítico (case_operational_assistant.py)
│     risco documentado; nenhuma decisão humana registrada; não é tarefa
│     agendada automaticamente por este roadmap
│
└── 🚫 Verificação ao vivo de Production
      NÃO VERIFICADA neste checkpoint; qualquer verificação ao vivo
      exige autorização humana específica
```
