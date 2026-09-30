# NEXT_STEP.md — Tarefa operacional corrente

## A. Finalidade

Este documento define a **única tarefa operacional corrente em foco**, no
sentido de `AGENTS.md` (Seção 4) e `DECISIONS.md` (`GOV-007`). Sua existência
**não constitui, por si só, autorização automática de execução** — qualquer
ação continua exigindo compatibilidade com `AGENTS.md`/`DECISIONS.md` e
autorização humana explícita quando exigida.

## B. Tarefa operacional corrente

**Tarefa corrente:** concluir a reconciliação documental do fechamento de
`OPS-005`, preservando a distinção entre histórico, estado comprovado e
trabalho futuro. Esta edição documental não autoriza nova implementação,
Git de escrita, Production ou integração externa.

A sequência técnica obrigatória definida por `OPS-005` foi executada e
concluída, nesta ordem:

- **BLOCO 1A:** PR #311,
  `c75d2e6c9a503bb1db7b76a690097b355bab7fa2` — infraestrutura de testes
  backend tornada hermética, com PostgreSQL de teste isolado, configuração
  de pytest e suporte específico aos testes PostgreSQL;
- **BLOCO 2:** PR #312,
  `29f7bd45b729766417781a80d7dfff56ddb3aa49` — RLS PostgreSQL tenant real
  e versionado, com migration, integração de tenant/session, segurança e
  testes associados;
- **BLOCO 1B:** PR #313,
  `1e7a686c602621ab5eaa86fdc9aaf3edd99e7833` — suíte backend completa
  incorporada ao CI, com `backend-full-suite` como status check obrigatório.
  Baseline final registrada: `316 passed, 0 failed`, `112 warnings`.

As decisões humanas **A = A1 (`ARCH-001`)** e **B = B2 (`ARCH-002`)**
permanecem registradas em `DECISIONS.md`. O fechamento técnico acima não
reescreve nem substitui essas decisões.

O problema de contrato registrado em `ARCH-002` continua fora desse
fechamento: `cases_per_month` é alias legado de `active_cases_limit`, enquanto
`remaining.cases` é calculado contra `cases_created`. A semântica de
`remaining.cases` / `cases_per_month` permanece **congelada** e exige decisão
humana própria futura antes de qualquer alteração.

`P-007` permanece resolvida (`OPS-003`). `P-002` foi resolvida em `OPS-004`
como prioridade e sua sequência técnica subsequente `OPS-005` foi concluída
pelos PRs #311, #312 e #313.

### Sequência de blocos aprovada — estado reconciliado

- **BLOCO 0** — governança/documentação anterior integrada.
- **BLOCO 1A** (`OPS-005`) — **CONCLUÍDO**, PR #311.
- **BLOCO 2** (`OPS-005`/`ARCH-001`) — **CONCLUÍDO**, PR #312.
- **BLOCO 1B** (`OPS-005`) — **CONCLUÍDO**, PR #313.
- **BLOCO 3** — segurança/LGPD — planejamento existente; **não autorizado
  automaticamente** por este documento.
- **BLOCO 4** — billing/Asaas — planejamento existente; **não autorizado
  automaticamente** por este documento.
- **BLOCO 5** — frontend faltante — planejamento existente; **não autorizado
  automaticamente** por este documento.
- **BLOCO 6** — gate de release — planejamento existente; **não autorizado
  automaticamente** por este documento.

A versão 16 do PostgreSQL usada nos testes não afirma a versão de Production.
Production permanece **NÃO VERIFICADA** neste checkpoint.

**PRÓXIMO PASSO:** concluir esta reconciliação documental. Depois disso,
qualquer nova frente técnica exige auditoria/proposta e autorização humana
específica; a conclusão de `OPS-005` não autoriza automaticamente BLOCO 3
nem qualquer outro bloco.

Nenhuma ação de Git de escrita, Production ou integração externa é
autorizada automaticamente por este estado.

## C. Estado atual do repositório

- Repositório principal: `/home/dilsondev/projetos/ia_trabalhista_robusta`.
- Em 2026-09-29, antes da criação desta branch documental, `main` local e
  `origin/main` foram comprovados sincronizados em
  `1e7a686c602621ab5eaa86fdc9aaf3edd99e7833` (PR #313).
- A reconciliação documental corrente ocorre na branch
  `docs/reconcile-ops005-completion-v1`.
- A sequência técnica `OPS-005` está integrada a `main`: BLOCO 1A via
  PR #311 (`c75d2e6c9a503bb1db7b76a690097b355bab7fa2`), BLOCO 2 via
  PR #312 (`29f7bd45b729766417781a80d7dfff56ddb3aa49`) e BLOCO 1B via
  PR #313 (`1e7a686c602621ab5eaa86fdc9aaf3edd99e7833`).
- Nesta reconciliação estão autorizadas somente alterações documentais em
  `PROJECT_STATE.md`, `NEXT_STEP.md` e `ROADMAP.md`. `DECISIONS.md`
  permanece inalterado.
- Até este checkpoint documental, não há autorização automática para
  staging, commit, push, PR, merge, deploy ou qualquer ação em Production.

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

No estado atual, a sequência `OPS-005` — BLOCO 1A → BLOCO 2 → BLOCO 1B —
já foi concluída e integrada pelos PRs #311, #312 e #313. A tarefa vigente é
concluir a reconciliação documental desse fechamento. Qualquer nova frente
técnica posterior depende de auditoria/proposta e autorização humana
específica; nenhuma é iniciada automaticamente.

## H. Pendências humanas após o fechamento técnico de OPS-005

`P-007` permanece resolvida (`OPS-003`). `P-002` foi decidida como prioridade
em `OPS-004`; A1 (`ARCH-001`) e B2 (`ARCH-002`) foram decididas por humano em
2026-09-25. A sequência técnica subsequente 1A → 2 → 1B, registrada em
`OPS-005`, foi concluída pelos PRs #311, #312 e #313.

Essa conclusão não resolve automaticamente as demais decisões pendentes.
O defeito de `remaining.cases` registrado em `ARCH-002` continua sem solução
decidida e sua semântica permanece congelada. Também permanecem abertas
`P-001`, `P-003` a `P-006` e `P-008` a `P-010`, conforme `DECISIONS.md`.

Nenhuma dessas pendências constitui autorização automática para iniciar uma
nova implementação.

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

- Tarefa em foco: **concluir a reconciliação documental do fechamento de
  `OPS-005`**.
- A sequência **BLOCO 1A → BLOCO 2 → BLOCO 1B** foi concluída e integrada:
  PR #311 → PR #312 → PR #313.
- Baseline final registrada do backend: **`316 passed, 0 failed`,
  `112 warnings`**.
- `backend-full-suite` está incorporado ao CI e foi configurado como status
  check obrigatório.
- `remaining.cases` / `cases_per_month` permanecem fora do fechamento de
  `OPS-005`, congelados e dependentes de decisão humana futura.
- Production permanece **NÃO VERIFICADA** neste checkpoint.
- Nenhum BLOCO 3–6 nem qualquer outra nova frente técnica é autorizado
  automaticamente pela conclusão de `OPS-005` ou por este documento.
- Este documento, por si só, não autoriza staging, commit, push, PR, merge,
  deploy, ação em Production ou integração externa.
