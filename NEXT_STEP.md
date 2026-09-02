# NEXT_STEP.md — Tarefa operacional corrente

## A. Finalidade

Este documento define a **única tarefa operacional corrente em foco**, no
sentido de `AGENTS.md` (Seção 4) e `DECISIONS.md` (`GOV-007`). Sua existência
**não constitui, por si só, autorização automática de execução** — qualquer
ação continua exigindo compatibilidade com `AGENTS.md`/`DECISIONS.md` e
autorização humana explícita quando exigida.

## B. Tarefa operacional corrente

**Nenhuma tarefa técnica está em foco.**

A implantação inicial da governança está materialmente concluída: 7/7
arquivos criados e validados no worktree de governança. `PROJECT_STATE.md`,
`ROADMAP.md` e `ARCHITECTURE.md` já foram atualizados e verificados; este
`NEXT_STEP.md` é atualizado por último.

Com a verificação em leitura desta versão final de `NEXT_STEP.md` concluída
com sucesso, o fechamento documental está concluído. Até essa verificação,
considerar o fechamento **em verificação final**.

Nenhuma tarefa técnica nova foi selecionada como consequência disso.
Nenhuma feature, refatoração ou frente técnica está autorizada por
consequência. `P-002` (prioridade do próximo ciclo) e `P-007`
(destino/fechamento da frente local atual) permanecem pendentes, assim como
as demais pendências registradas em `DECISIONS.md`.

Nenhuma ação de Git de escrita, Production ou integração externa é
autorizada automaticamente por este estado.

**NENHUMA TAREFA TÉCNICA AUTORIZADA — AGUARDANDO DECISÃO HUMANA SOBRE A
PRÓXIMA FRENTE.**

## C. Estado atual da implantação

- Worktree de governança:
  `/home/dilsondev/projetos/ia_trabalhista_robusta-governance-docs-v1`
- Branch de governança: `chore/governance-docs-v1`, nascida limpa no
  baseline aprovado `4e9d22fdae99fc717192ea5b6b96214f61d70628`.
- **7/7 arquivos materialmente criados e validados** (untracked, não
  staged, não commitados, sem push, sem PR): `AGENTS.md`,
  `PROJECT_STATE.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `DECISIONS.md`,
  `NEXT_STEP.md`, `CLAUDE.md`.
- `PROJECT_STATE.md`, `ROADMAP.md` e `ARCHITECTURE.md` já receberam as
  correções temporais necessárias e foram validados antes desta edição
  final de `NEXT_STEP.md`.
- Este `NEXT_STEP.md` é atualizado por último.
- Com a verificação em leitura desta versão final concluída com sucesso,
  o fechamento documental está concluído. Até essa verificação, considerar
  o fechamento **em verificação final**.

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
- Nenhum fechamento, commit, push ou PR da branch local
  `fix/editor-civil-professional-risk-specialization-v1` — ela e seus dois
  arquivos modificados (`case_operational_assistant.py`,
  `test_massive_multicase_all_blocks_regression.py`) **continuam fora do
  escopo desta implantação de governança e não devem ser tocados.**
- Nenhum `commit`, `push`, `PR`, `merge`, `pull`, `tag`, `release` ou
  `deploy` do próprio worktree de governança, salvo autorização humana
  explícita e específica para esse ato (fora do escopo desta tarefa).
- Nenhum acesso a Production, integração externa, teste, build, banco ou
  migração nesta etapa.

## F. Critérios de conclusão MATERIAL da implantação

A implantação inicial da governança é considerada **materialmente concluída**
quando:

1. `CLAUDE.md` tiver sido proposto, aprovado, criado e validado conforme o
   processo já aprovado (proposta → aprovação → escrita → verificação em
   leitura); e
2. uma verificação em leitura confirmar os 7 de 7 arquivos materializados no
   worktree de governança, sem alterações indevidas nos demais arquivos e
   sem staging/commit/push não autorizados.

Ao atingir 7/7:
- registrar que a implantação está **materialmente concluída**;
- **PARAR**;
- **não iniciar automaticamente** o fechamento documental da Seção G;
- **não iniciar** nenhuma tarefa técnica;
- **aguardar nova instrução humana específica**.

A etapa de fechamento documental (Seção G) é **separada e posterior** à
conclusão material — não é um terceiro critério desta seção, e não ocorre
como consequência automática de atingir 7/7. Isso preserva a distinção:

7/7 materializados e validados
≠ fechamento documental já executado
≠ autorização para próxima frente técnica.

Cada critério acima exige evidência objetiva, rastreável e válida para o
estado relevante. Evidência de checkpoint anterior pode continuar válida
quando permanecer válida pelos critérios de `AGENTS.md` Seção 7 /
`DECISIONS.md` `GOV-006`. Memória de agente ou afirmação de conversa nunca
substitui evidência. Se houver mudança relevante, regressão, dúvida material
ou mudança de checkpoint que invalide a evidência, devem ser refeitas as
verificações pertinentes.

## G. Regra de parada após 7/7

Ao atingir 7 de 7 arquivos materialmente criados e validados, o processo
**para** — nenhuma ação subsequente é automática. Antes de qualquer nova
tarefa técnica:

1. Deve haver uma **etapa documental separada de fechamento da implantação**,
   destinada a atualizar checkpoints que tenham ficado temporalmente
   desatualizados pela própria sequência de criação dos arquivos. Nesta
   implantação, essa necessidade ocorreu e os checkpoints afetados foram
   corrigidos antes do encerramento documental final.
2. Essa etapa de fechamento é, ela própria, uma tarefa que segue o mesmo
   ciclo de proposta → aprovação → escrita → verificação — não ocorre
   silenciosamente como efeito colateral da criação de `CLAUDE.md`.
3. Somente depois desse fechamento documental, o responsável humano decide
   qual será a próxima tarefa técnica — este documento não a escolhe, não a
   sugere como decidida e não a inicia.

## H. Pendências humanas que impedem escolha automática da próxima frente

Nenhum agente de IA escolhe a próxima frente técnica por conta própria. Em
especial, as seguintes pendências de `DECISIONS.md` seguem abertas e devem
ser consideradas pelo humano responsável quando essa escolha for feita:

- **P-002** — prioridade do próximo ciclo de desenvolvimento.
- **P-007** — destino/fechamento da frente local atual.
- Demais pendências (`P-001`, `P-003` a `P-006`, `P-008` a `P-010`) também
  permanecem em aberto e podem condicionar ou informar essa escolha futura.

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

- Tarefa em foco: **nenhuma tarefa técnica; implantação inicial
  materialmente concluída; fechamento documental em verificação final.**
- 7/7 arquivos materialmente criados e validados; `PROJECT_STATE.md`,
  `ROADMAP.md` e `ARCHITECTURE.md` atualizados e verificados; este
  `NEXT_STEP.md` atualizado por último.
- Com a verificação em leitura desta versão bem-sucedida, o fechamento
  documental está concluído.
- **NENHUMA TAREFA TÉCNICA AUTORIZADA — AGUARDANDO DECISÃO HUMANA SOBRE A
  PRÓXIMA FRENTE**, considerando especialmente `P-002`, `P-007` e as
  demais pendências de `DECISIONS.md`.
- Este documento, por si só, não autoriza nenhuma ação de Git de escrita,
  Production ou integração externa.
