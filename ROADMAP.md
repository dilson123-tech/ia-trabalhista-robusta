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

- ✅ Autenticação JWT, RBAC, isolamento multi-tenant (incluindo RLS em
  Postgres) — implementado e testado, per `MVP_VALIDATION_MATRIX.md`
  (itens `[x]` nas seções 2 e 3) e suíte de testes (`test_rls_isolation.py`,
  `test_tenant_isolation.py`, `test_multi_tenant_isolation.py`).
- ✅ Fluxo executivo caso → análise → resumo → relatório → PDF — implementado
  e testado, per `MVP_VALIDATION_MATRIX.md` (seções 4–6) e serviços auditados
  (`decision_engine.py`, `report_engine.py`, `pdf_executive.py`).
- ✅ Health/readiness/CI/smoke — implementado e testado, per
  `.github/workflows/ci.yml` e seção 1 da matriz.
- ✅ Cobertura extensa de especialização trabalhista e consumidor no editor
  assistido — implementado, com cadeia de PRs mesclados (#284–#299) e testes
  correspondentes (`test_editor_labor_template_routing.py` e a família
  `test_editor_civil_*`/consumidor).
- ✅ Billing técnico (checkout + webhook Asaas com verificação de token) —
  implementado e integrado no código (`payment_checkout.py`, `webhooks.py`);
  ver Seção I para o limite exato dessa comprovação.
- ✅ **Governança documental persistente de IA** — implantação inicial
  MATERIAL concluída: 7/7 arquivos materializados e validados no worktree
  `chore/governance-docs-v1`; nenhum staged/commitado/enviado por push/com
  PR. Isso registra somente a conclusão documental da implantação e não
  autoriza nova frente técnica nem resolve `P-002`/`P-007`.

## D. Frentes em andamento

- 🔄 **Especialização cível — restrição/risco profissional (LGPD)**: frente
  local aberta na branch `fix/editor-civil-professional-risk-specialization-v1`,
  que permanece no repositório/worktree original
  (`/home/dilsondev/projetos/ia_trabalhista_robusta`), com os dois arquivos
  locais não commitados registrados em `PROJECT_STATE.md` (Seções B–C). É a
  **governança** — não essa frente — que está sendo implantada em worktree
  separado, justamente para não misturar as duas. ⚠️ O fechamento dessa frente
  (commit/PR) é decisão humana pendente — este roadmap não a decide nem a
  agenda automaticamente.
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
  roadmap** (regra explícita) — depende de decisão humana ainda pendente.

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
ou com PR aberto. **Implantação MATERIAL concluída** — isso não altera
prioridades técnicas nem resolve `P-002`/`P-007` em `DECISIONS.md`, que
permanecem pendentes.

## L. Decisões humanas que bloqueiam ou condicionam fases

As decisões abaixo estão formalizadas com IDs `P-*` em `DECISIONS.md`, que é
a fonte normativa. Esta seção apenas resume o que cada pendência bloqueia ou
condiciona neste roadmap; não resolve nenhuma delas.

- **Nomenclatura oficial do produto — `P-001`** — condiciona comunicação
  externa e comercial consistente (Seção B).
- **Prioridade do próximo ciclo de desenvolvimento — `P-002`** — bloqueia o
  início de qualquer nova frente técnica pós-governança (Seção E, 4 opções
  em aberto).
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
- **Destino/fechamento da frente local aberta — `P-007`** — enquanto houver
  trabalho local não relacionado/não commitado nessa working tree, outra
  frente não deve ser misturada nela; trabalho separado pode exigir
  branch/worktree apropriado e autorização conforme
  `AGENTS.md`/`DECISIONS.md`. O destino da frente atual continua decisão
  humana pendente (Seção D).
- **Higiene de `.env`/`.env.bak*` — `P-008`** — condiciona o fechamento de
  segurança operacional (Seção F).

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
├── ✅ Infra base (auth, tenant, RLS, health/ready, CI, plans/limits)
│     estimativa: ~90% — quase todos os itens [x] nas seções 1–3 da matriz
│
├── ✅ Fluxo executivo (análise → resumo → relatório → PDF)
│     estimativa: ~85% — quase todos os itens [x] na seção 6 da matriz
│
├── 🔄 Motor de especialização jurídica (copiloto/editor)
│     estimativa: ~65% — cobertura extensa trabalhista/consumidor; cível em
│     expansão ativa (frente local aberta, não commitada); criminal V1 parcial
│
├── 🔄 Billing/Asaas
│     estimativa: ~70% no código (implementado/integrado/testado);
│     produção "documentada", não verificada ao vivo por este roadmap
│
├── ✅ Governança documental de IA
│     progresso documental: 7 de 7 arquivos materializados e validados
│     (AGENTS.md, PROJECT_STATE.md, ROADMAP.md, ARCHITECTURE.md,
│     DECISIONS.md, NEXT_STEP.md, CLAUDE.md), nenhum staged/commitado/
│     enviado por push/com PR. Implantação MATERIAL concluída. Este
│     número mede apenas o progresso da implantação documental da
│     governança — não percentual de conclusão técnica do produto, nem
│     resolução de P-002/P-007 em DECISIONS.md, que permanecem
│     pendentes.
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
      não autorizada nesta etapa de governança
```
