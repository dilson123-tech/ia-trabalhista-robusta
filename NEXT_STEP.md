# NEXT_STEP.md — Tarefa operacional corrente

## A. Finalidade

Este documento define a **única tarefa operacional corrente em foco**, no
sentido de `AGENTS.md` (Seção 4) e `DECISIONS.md` (`GOV-007`). Sua existência
**não constitui, por si só, autorização automática de execução** — qualquer
ação continua exigindo compatibilidade com `AGENTS.md`/`DECISIONS.md` e
autorização humana explícita quando exigida.

## B. Tarefa operacional corrente

**Sequência obrigatória, nesta ordem:**

1. **Fechar este adendo documental A1/B2** (registro das decisões humanas
   A1/B2 em `DECISIONS.md`, `PROJECT_STATE.md`, `NEXT_STEP.md` e
   `ROADMAP.md`), mediante revisão humana (DICO/ChatGPT). Staging, commit,
   push e PR deste adendo exigem autorização humana específica para
   cada ato.
2. **Preparar o BLOCO 1** (suíte hermética + baseline real + CI completo):
   somente planejamento/análise em leitura, quando solicitado pelo
   responsável humano. **Preparação não é implementação.**
3. **Somente depois**, e mediante nova autorização humana específica para
   cada ato, implementar o BLOCO 1 (criar branch técnica, alterar
   testes/código/CI, executar `pytest`).

As decisões humanas **A** e **B** de `OPS-004` foram tomadas em
2026-09-25 (DICO/ChatGPT) e registradas em `DECISIONS.md`:

- **A = A1 (`ARCH-001`)** — implementar RLS PostgreSQL real e versionado,
  mantendo o isolamento multi-tenant em nível de aplicação
  (`scoped_query`) como camada adicional. Requisitos da implementação
  futura: policies versionadas por migration; role de aplicação
  compatível com `ARCH-001` — não superusuária, sem `BYPASSRLS`, com
  ownership/`FORCE ROW LEVEL SECURITY` tratado explicitamente; isolamento
  testado em PostgreSQL real; cobertura em CI. **RLS não implementado.**
- **B = B2 (`ARCH-002`)** — `limits_for(plan_type)` é a fonte oficial da
  verdade para limites de plano e enforcement. `Subscription.case_limit`
  é campo legado/informativo (não é enforcement, não é override
  contratual, não é fonte oficial do limite admin); a coluna **não** é
  removida (remoção/deprecação futura exige análise separada).
  `test_admin_tenant_usage_full_returns_consolidated_view` deverá ser
  reconciliado com B2, sem `50` hardcoded e sem depender do `.env` local.
  **Nada foi alterado em código ou testes.**

Problema técnico registrado para o BLOCO 1 (achado em `ARCH-002`, **sem
solução decidida**): `cases_per_month` é alias legado de
`active_cases_limit`, mas `remaining.cases` é calculado contra o contador
mensal `cases_created`, misturando limite de casos **ATIVOS** com casos
**CRIADOS NO MÊS**.

`P-007` foi resolvida (`OPS-003`): código/produto integrado a `main` via
PR #306; fechamento documental integrado a `main` via PR #307.
`P-002` foi resolvida em `OPS-004` **apenas como prioridade**: restaurar
uma baseline confiável de testes e isolamento multi-tenant antes de novas
features; a reconciliação documental correspondente foi integrada a `main`
via PR #308. A solução técnica das duas falhas conhecidas
(`test_admin_tenant_usage_full_returns_consolidated_view` e
`test_rls_isolation`) agora tem direção decidida (B2 e A1,
respectivamente), mas **não foi implementada**.

### Sequência de blocos aprovada (planejamento, não autorização)

- **BLOCO 0** — governança/documentação coerente (integrado via PR #308; este adendo registra A1/B2).
- **BLOCO 1** — suíte hermética + baseline real + CI completo.
- **BLOCO 2** — isolamento PostgreSQL/tenant comprovado.
- **BLOCO 3** — segurança/LGPD.
- **BLOCO 4** — billing/Asaas.
- **BLOCO 5** — frontend faltante.
- **BLOCO 6** — gate de release.

**Nenhum bloco técnico (BLOCO 1 a 6) está autorizado para implementação
por esta edição.** A preparação (planejamento em leitura) do BLOCO 1 é o
foco atual.
Nenhuma branch técnica foi criada ou autorizada. O nome
`fix/ci-plan-limit-test-and-rls-role-isolation-v1`, proposto
anteriormente, foi superado pela auditoria-mestra, nunca foi criado e não
constitui frente autorizada.

Nenhuma ação de Git de escrita, Production ou integração externa é
autorizada automaticamente por este estado.

**PRÓXIMO PASSO: FECHAR ESTE ADENDO DOCUMENTAL A1/B2 → PREPARAR O BLOCO 1
(SEM IMPLEMENTAR) → SOMENTE COM NOVA AUTORIZAÇÃO ESPECÍFICA, IMPLEMENTAR O
BLOCO 1.**

## C. Estado atual do repositório

- Repositório principal: `/home/dilsondev/projetos/ia_trabalhista_robusta`,
  branch `main`, observada em 2026-09-25 em
  `55945775ffeda2a8ea5c033bd8569d156f0972ac` (commit
  `docs(governance): reconcile P-002 with master audit (#308)`), igual a
  `origin/main` local, working tree limpo antes desta edição — valor
  observado, a reverificar via Git em cada sessão (ver `PROJECT_STATE.md`,
  Seção B).
- Os 7 arquivos de governança estão commitados e integrados em `main`
  (PR #305); o fechamento de `P-007` (PR #306, produto) e seu registro
  documental (PR #307, `DECISIONS.md`) também estão integrados em `main`;
  a reconciliação de `P-002` com a auditoria-mestra foi integrada em
  `main` via PR #308.
- O worktree de governança temporário e a branch
  `docs/close-p007-decision-v1` foram removidos após comprovação de
  equivalência material de conteúdo.
- Nenhuma branch técnica para `P-002`/BLOCO 1 foi criada.
- Esta atualização documental (registro de A1/B2) está sendo feita
  diretamente no working tree de `main`, com alterações locais não
  commitadas em `DECISIONS.md`, `PROJECT_STATE.md`, `NEXT_STEP.md` e
  `ROADMAP.md`; sem staging, commit ou push.

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

1. fechar este adendo documental A1/B2;
2. preparar o BLOCO 1 (planejamento em leitura, sem implementar);
3. somente depois, mediante nova autorização específica, implementar o
   BLOCO 1.

## H. Pendências humanas relacionadas ao início da implementação

`P-007` (destino da frente local anterior) foi decidida (`OPS-003`).
`P-002` foi decidida apenas como prioridade (`OPS-004`). As decisões
técnicas **A** (modelo de isolamento) e **B** (semântica do limite admin)
foram decididas por humano em 2026-09-25: **A1** (`ARCH-001`) e **B2**
(`ARCH-002`). Essas decisões **não** autorizam, por si só, a implementação
do BLOCO 1/BLOCO 2. O defeito de `remaining.cases` registrado em `ARCH-002`
não tem solução decidida. As demais pendências seguem abertas e não são
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

- Tarefa em foco: **fechar a atualização documental que registra A1/B2
  e, em seguida, preparar (sem implementar) o BLOCO 1.**
- `P-007` resolvida e integrada em `main`; `P-002` resolvida apenas como
  prioridade (`OPS-004`); A decidida como A1 (`ARCH-001`) e B decidida
  como B2 (`ARCH-002`) — nenhuma das duas implementada.
- Último resultado conhecido da suíte global do backend: `304 passed,
  2 failed` em 306 testes (registrado em `OPS-003`; não reexecutado).
  Production: **NÃO VERIFICADA**.
- **BLOCO 1 NÃO IMPLEMENTADO E NÃO AUTORIZADO PARA IMPLEMENTAÇÃO —
  AGUARDANDO REVISÃO DESTA ATUALIZAÇÃO DOCUMENTAL E NOVA AUTORIZAÇÃO
  HUMANA ESPECÍFICA** para criar branch técnica, alterar
  testes/código/banco/CI, criar migration ou executar testes.
- Este documento, por si só, não autoriza nenhuma ação de Git de escrita,
  Production ou integração externa.
