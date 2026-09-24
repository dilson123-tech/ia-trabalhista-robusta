# NEXT_STEP.md — Tarefa operacional corrente

## A. Finalidade

Este documento define a **única tarefa operacional corrente em foco**, no
sentido de `AGENTS.md` (Seção 4) e `DECISIONS.md` (`GOV-007`). Sua existência
**não constitui, por si só, autorização automática de execução** — qualquer
ação continua exigindo compatibilidade com `AGENTS.md`/`DECISIONS.md` e
autorização humana explícita quando exigida.

## B. Tarefa operacional corrente

**Sequência obrigatória, nesta ordem:**

1. **Fechar esta atualização documental** (reconciliação de
   `DECISIONS.md`, `PROJECT_STATE.md`, `NEXT_STEP.md` e `ROADMAP.md` com a
   auditoria-mestra de 2026-09-24), mediante revisão humana
   (DICO/ChatGPT). Staging, commit, push e PR desta atualização exigem
   autorização humana específica para cada ato.
2. **DICO/ChatGPT decidem as pendências A e B** registradas em `OPS-004`
   (`DECISIONS.md`):
   - **A — Modelo de isolamento multi-tenant:** RLS PostgreSQL real e
     versionado **ou** isolamento formalmente somente em nível de aplicação
     (com arquitetura, testes e documentação ajustados). **Pendente
     (humana).**
   - **B — Semântica do limite na visão admin:** `Subscription.case_limit`
     **ou** limite derivado de `limits_for(plan_type)`. **Pendente
     (humana).**
3. **Somente depois**, e mediante nova autorização humana específica,
   iniciar o primeiro bloco técnico (BLOCO 1).

`P-007` foi resolvida (`OPS-003`): código/produto integrado a `main` via
PR #306; fechamento documental integrado a `main` via PR #307.
`P-002` foi resolvida em `OPS-004` **apenas como prioridade**: restaurar
uma baseline confiável de testes e isolamento multi-tenant antes de novas
features. A solução técnica das duas falhas conhecidas
(`test_admin_tenant_usage_full_returns_consolidated_view` e
`test_rls_isolation`) **não está decidida** e depende de A e B.

### Sequência de blocos aprovada (planejamento, não autorização)

- **BLOCO 0** — governança/documentação coerente (esta atualização).
- **BLOCO 1** — suíte hermética + baseline real + CI completo.
- **BLOCO 2** — isolamento PostgreSQL/tenant comprovado.
- **BLOCO 3** — segurança/LGPD.
- **BLOCO 4** — billing/Asaas.
- **BLOCO 5** — frontend faltante.
- **BLOCO 6** — gate de release.

**Nenhum bloco técnico (BLOCO 1 a 6) está autorizado por esta edição.**
Nenhuma branch técnica foi criada ou autorizada. O nome
`fix/ci-plan-limit-test-and-rls-role-isolation-v1`, proposto
anteriormente, foi superado pela auditoria-mestra, nunca foi criado e não
constitui frente autorizada.

Nenhuma ação de Git de escrita, Production ou integração externa é
autorizada automaticamente por este estado.

**PRÓXIMO PASSO: FECHAR ESTA ATUALIZAÇÃO DOCUMENTAL → DECISÃO HUMANA DE A E
B → SOMENTE ENTÃO, COM NOVA AUTORIZAÇÃO ESPECÍFICA, BLOCO 1.**

## C. Estado atual do repositório

- Repositório principal: `/home/dilsondev/projetos/ia_trabalhista_robusta`,
  branch `main`, sincronizada local e remotamente em
  `0fc0755d7de4ced50400f6e297a99338f6d9cd50` (ver `PROJECT_STATE.md`,
  Seção B, para o protocolo de reverificação em cada sessão).
- Os 7 arquivos de governança estão commitados e integrados em `main`
  (PR #305); o fechamento de `P-007` (PR #306, produto) e seu registro
  documental (PR #307, `DECISIONS.md`) também estão integrados em `main`.
- O worktree de governança temporário e a branch
  `docs/close-p007-decision-v1` foram removidos após comprovação de
  equivalência material de conteúdo.
- Nenhuma branch técnica para `P-002` foi criada.
- Esta atualização documental está sendo feita na branch
  `docs/resolve-p002-governance-v1` (criada a partir de `main` em
  `0fc0755d7de4ced50400f6e297a99338f6d9cd50`), com alterações locais não
  commitadas em `DECISIONS.md`, `PROJECT_STATE.md`, `NEXT_STEP.md` e
  `ROADMAP.md` — valor observado em 2026-09-24, a reverificar via Git.

## D. Escopo permitido no estado de espera

Enquanto nenhuma nova tarefa técnica tiver sido escolhida e, quando
aplicável, explicitamente autorizada pelo responsável humano:

- são permitidas verificações em leitura necessárias para compreender o
  estado real do repositório e da governança;
- análise ou proposta de próxima frente somente quando solicitada pelo
  responsável humano;
- nenhuma edição técnica ou documental começa automaticamente;
- qualquer futura tarefa deve ser compatível com `AGENTS.md`,
  `DECISIONS.md` e com o `NEXT_STEP.md` vigente, além das autorizações
  humanas aplicáveis.

A existência de uma tarefa em `NEXT_STEP.md` não constitui, por si só,
autorização automática de execução.

## E. Ações explicitamente fora do escopo desta tarefa

Nenhuma das ações abaixo é autorizada automaticamente pela conclusão
material da implantação (7/7) nem pelo fechamento documental:

- Nenhuma feature de produto.
- Nenhuma refatoração (incluindo `case_operational_assistant.py`, `P-003`).
- Nenhuma nova frente técnica.
- Nenhum fechamento, commit, push ou PR de branch técnica sem autorização
  específica para o ato — a antiga branch de produto
  `fix/editor-civil-professional-risk-specialization-v1` já foi encerrada e
  removida (`P-007`, resolvida em `OPS-003`) e não existe mais; esta regra
  permanece como princípio geral para qualquer branch/frente de produto
  atualmente em andamento.
- Nenhum `commit`, `push`, `PR`, `merge`, `pull`, `tag`, `release` ou
  `deploy` relacionado a esta atualização documental ocorre automaticamente;
  cada ato exige autorização humana explícita e específica.
- Nenhum acesso a Production, integração externa, teste, build, banco ou
  migração nesta etapa.

## F. Critério histórico de conclusão MATERIAL da implantação inicial

A implantação inicial da governança persistente já foi materialmente concluída
e integrada em `main`. Este bloco permanece somente como registro histórico do
critério usado naquele rollout.

Na implantação inicial, a conclusão material exigia:

1. os 7 arquivos de governança propostos, aprovados, criados e validados;
2. verificação objetiva de que os 7 arquivos estavam presentes e coerentes;
3. ausência de alterações indevidas, staging, commit ou push não autorizados;
4. parada obrigatória antes de qualquer nova frente técnica.

Esse marco histórico não constitui tarefa atual, não exige recriação de
worktree e não autoriza automaticamente nova implementação.

O estado operacional corrente é definido pelas Seções B, C, H e J deste
documento, em conjunto com `PROJECT_STATE.md` e `DECISIONS.md`.

## G. Regra histórica de parada após a implantação inicial

Durante o rollout inicial, ao atingir 7 de 7 arquivos de governança criados e
validados, o processo deveria parar antes de qualquer nova frente técnica.
Essa regra foi aplicada; a implantação foi posteriormente integrada em `main`
e o worktree temporário de governança foi removido.

O princípio continua válido: conclusão documental nunca autoriza, por si só,
uma nova tarefa técnica.

No estado atual, a sequência vigente é a definida na Seção B:

1. fechar esta atualização documental;
2. obter as decisões humanas A e B de `OPS-004`;
3. somente depois, mediante nova autorização específica, iniciar o BLOCO 1.

## H. Pendências humanas relacionadas ao início da implementação

`P-007` (destino da frente local anterior) foi decidida (`OPS-003`).
`P-002` foi decidida apenas como prioridade (`OPS-004`). As decisões
técnicas **A** (modelo de isolamento) e **B** (semântica do limite admin),
registradas em `OPS-004`, permanecem **pendentes (humanas)** e condicionam
o início do BLOCO 1/BLOCO 2. As demais pendências seguem abertas e não são
resolvidas nem antecipadas por este documento: `P-001`, `P-003` a `P-006`,
`P-008` a `P-010`.

## I. Evidência necessária para qualquer futura declaração de conclusão

- A regressão direcionada `108 passed, 24 warnings`, já registrada em
  `PROJECT_STATE.md` (Seção D), cobre exatamente os quatro arquivos de teste
  ali listados. **Não deve ser tratada, nesta tarefa ou em nenhuma futura,
  como suíte completa ou validação geral do produto.**
- Qualquer declaração futura de conclusão desta tarefa, ou de qualquer nova
  tarefa técnica, deve seguir a regra de evidência de `AGENTS.md` (Seção 7)
  e `GOV-006` de `DECISIONS.md`: evidência objetiva, rastreável, vinculada a
  checkpoint conhecido, reexecutada se o código relevante mudar. Memória de
  agente ou afirmação de conversa não substitui evidência.

## J. Status operacional

- Tarefa em foco: **fechar a atualização documental (BLOCO 0) e obter a
  decisão humana de A e B (`OPS-004`).**
- `P-007` resolvida e integrada em `main`; `P-002` resolvida apenas como
  prioridade (`OPS-004`); A e B pendentes (humanas).
- Último resultado conhecido da suíte global do backend: `304 passed,
  2 failed` em 306 testes (registrado em `OPS-003`; não reexecutado).
  Production: **NÃO VERIFICADA**.
- **NENHUM BLOCO TÉCNICO AUTORIZADO — AGUARDANDO REVISÃO DESTA ATUALIZAÇÃO
  DOCUMENTAL, DECISÃO HUMANA DE A E B E NOVA AUTORIZAÇÃO HUMANA
  ESPECÍFICA** para criar branch técnica, alterar testes/código/banco ou
  executar testes.
- Este documento, por si só, não autoriza nenhuma ação de Git de escrita,
  Production ou integração externa.
