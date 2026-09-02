# CLAUDE.md — Entrada operacional do Claude Code

## A. Papel deste arquivo

Este é o **ponto de entrada específico do Claude Code** neste repositório.
Ele ensina como iniciar e conduzir uma sessão aqui de forma segura e
compatível com os demais documentos de governança. Ele **não substitui**
`AGENTS.md` e **não duplica** integralmente `PROJECT_STATE.md`,
`ROADMAP.md`, `ARCHITECTURE.md`, `DECISIONS.md` ou `NEXT_STEP.md` — aponta
para eles.

A nomenclatura oficial do produto permanece decisão humana pendente
(`P-001` em `DECISIONS.md`); este arquivo é deliberadamente neutro quanto a
esse ponto.

## B. Autoridade e precedência

- `AGENTS.md` contém as **regras permanentes** de conduta e segurança e tem
  **precedência máxima** sobre processo e conduta.
- Em qualquer conflito entre este `CLAUDE.md` e `AGENTS.md`, **`AGENTS.md`
  prevalece**.
- A hierarquia completa de precedência entre os documentos de governança
  está definida em `AGENTS.md`, Seção 4, e não é repetida aqui.

## C. Protocolo de início de sessão

Ao começar a trabalhar neste repositório:

1. **Ler `AGENTS.md` primeiro.**
2. Obter o estado real diretamente do Git, **sem presumir `PROJECT_STATE.md`
   como estado corrente**:

```bash
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Esses comandos observam apenas o estado local já disponível. Não executar
`git fetch`, `pull` ou qualquer ação de rede/escrita automaticamente.

## D. Ordem de leitura após a verificação Git

1. `DECISIONS.md` — decisões humanas aprovadas e pendentes.
2. `PROJECT_STATE.md` — checkpoint documental, sempre confrontado com o
   Git/código real observado no passo C, nunca tratado como atual por si só.
3. `NEXT_STEP.md` — única tarefa operacional corrente em foco; sua
   existência **não constitui autorização automática**.
4. `ARCHITECTURE.md` — arquitetura comprovada/documentada.
5. `ROADMAP.md` — planejamento futuro; **nunca autorização automática de
   execução**.

## E. Tratamento de divergências

Se o Git/código real e a governança apresentarem divergência relevante (por
exemplo, `PROJECT_STATE.md` descrevendo um checkpoint que não bate com o
`git status` observado agora):

**PARAR. RELATAR. AGUARDAR orientação humana.**

Nunca corrigir silenciosamente `PROJECT_STATE.md` ou qualquer outro
documento para "resolver" a divergência (`AGENTS.md`, Seção 4).

## F. Tarefa corrente / NEXT_STEP

- `NEXT_STEP.md` define o foco, **não** a autorização. Antes de executar
  qualquer ação, conferir:
  - se está dentro do escopo de `NEXT_STEP.md`;
  - se `AGENTS.md` permite;
  - se `DECISIONS.md` não bloqueia/condiciona;
  - se existe autorização humana aplicável para o ato específico.
- `ROADMAP.md` não permite avançar automaticamente: concluir uma tarefa
  nunca autoriza iniciar a próxima por inferência.

## G. Decisões e pendências

- Decisões aprovadas (`GOV-*`, `SEC-*`, `OPS-*`, `LEG-*`, `ARCH-*`, `PROD-*`,
  `DATA-*`) e pendências humanas (`P-001` a `P-010`, e as que vierem a ser
  registradas) vivem em `DECISIONS.md` — não são copiadas nem decididas
  aqui.
- Nenhuma pendência `P-*` é considerada resolvida por sugestão de um agente
  de IA; só por decisão humana explícita, registrada em `DECISIONS.md`.

## H. Segurança e proteção do working tree

- Antes de editar qualquer coisa: verificar branch/status, identificar
  alterações tracked/untracked já existentes, e **preservar** trabalho de
  outras frentes.
- Não usar `checkout`/`switch`/`stash`/`reset`/`clean`/`rebase`/`pull`, nem
  remover, sobrescrever ou limpar arquivos locais (tracked ou não), sem
  autorização apropriada (`AGENTS.md`, Seção 6).
- **Segredos:** nunca ler ou expor conteúdo sensível de `.env`,
  `.env.bak*`, tokens, chaves, senhas ou qualquer segredo. Respeitar
  integralmente `AGENTS.md` e as decisões `SEC-*` de `DECISIONS.md`.

## I. Trabalho jurídico e confiabilidade

- Não inventar: fatos, provas, valores, jurisprudência, conclusões
  jurídicas não sustentadas, estado de Production, sucesso de testes não
  executados/comprovados, ou decisões humanas.
- A IA pode analisar, estruturar alternativas, apontar riscos, comparar
  hipóteses e apresentar recomendações fundamentadas — mas **não toma,
  autonomamente, a decisão jurídica final**.
- Revisão e decisão profissional do advogado responsável permanecem
  **obrigatórias** antes de protocolo, entrega ao cliente ou uso externo
  relevante (`AGENTS.md`, Seção 2; `LEG-001`/`LEG-002` em `DECISIONS.md`).

## J. Evidência e conclusão

- Só declarar uma tarefa concluída com evidência objetiva, rastreável e
  válida para o estado relevante do código, conforme `AGENTS.md` Seção 7 e
  `DECISIONS.md` `GOV-006`.
- Evidência de checkpoint anterior pode continuar válida nesses mesmos
  critérios — mas **memória do Claude, resumo automático, recap ou
  conversa anterior nunca constitui evidência por si só.**
- Mudança relevante no código, dúvida material ou regressão exige
  reexecução das verificações pertinentes antes de qualquer nova conclusão.

## K. Ações sensíveis

Não executar por iniciativa própria: `git add`, `commit`, `push`, `merge`,
`pull`, `tag`, `release`, `deploy`, acesso a Production, migrações, seeds,
integrações externas, ou qualquer alteração de dados reais. Seguir as
autorizações aplicáveis em `AGENTS.md`/`DECISIONS.md` para cada ato
específico.

`git fetch` e qualquer outra atualização de referência remota/rede também
não devem ser executados por iniciativa própria — isso não equivale a
`commit` ou `push` em gravidade, mas é uma ação de rede que pode alterar
referências remotas locais (ver Seção C) e, como as demais desta lista,
deve respeitar a autorização aplicável antes de ser executada.

## L. Relato de início/fim de sessão

Ao iniciar uma sessão relevante, apresentar de forma compacta:

- repositório/worktree observado;
- branch observada;
- HEAD observado;
- `origin/main` observado localmente;
- working tree (limpo ou com alterações, e quais);
- divergências relevantes (se houver, ver Seção E);
- `NEXT_STEP.md` observado;
- decisões `P-*` que condicionem a tarefa;
- evidência disponível e seu limite.

Esse relato **não** atualiza automaticamente nenhum arquivo de governança —
é apenas informativo, salvo tarefa autorizada especificamente para isso.

## M. Regra especial de conclusão 7/7 desta implantação inicial

A criação e validação de `CLAUDE.md` materializa o sétimo e último arquivo
previsto para esta implantação inicial. Quando `CLAUDE.md` estiver criado e
validado, o Claude deve:

- somente **RELATAR** que os 7/7 arquivos estão materialmente criados e
  validados;
- **PARAR**;
- **não** transformar o fechamento documental em uma nova tarefa por conta
  própria;
- **não** propor ou iniciar `NEXT_STEP` técnico automaticamente;
- **não** editar `PROJECT_STATE.md`, `ROADMAP.md`, `NEXT_STEP.md`,
  `DECISIONS.md` ou qualquer outro documento como consequência automática
  da criação de `CLAUDE.md`;
- **não** iniciar feature, refatoração ou outra frente técnica;
- **não** tocar na branch/frente local de produto registrada no checkpoint
  operacional vigente (`PROJECT_STATE.md`/`NEXT_STEP.md`), nem em seus
  arquivos locais modificados;
- **não** fazer staging, commit, push ou PR;
- **aguardar nova instrução humana específica.**

A etapa posterior de fechamento documental é separada, conforme
`NEXT_STEP.md` (Seções F–G), e não ocorre automaticamente.

## N. Limites do `CLAUDE.md`

Este arquivo **não fixa como verdade permanente**: hash atual, branch
atual, quantidade atual de testes, estado atual de Production, "working
tree limpo", ou percentuais de conclusão do produto. Esses dados são
sempre observados dinamicamente (Seção C) ou registrados em checkpoints
apropriados (`PROJECT_STATE.md`), nunca copiados para cá como fato fixo.
Este documento não decide nenhuma pendência de `DECISIONS.md` e não
autoriza, por si só, nenhuma ação sensível listada na Seção K.
