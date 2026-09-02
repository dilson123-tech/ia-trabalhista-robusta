# DECISIONS.md — Registro de decisões e pendências

## A. Finalidade

Este documento registra, de forma rastreável e datada:

1. decisões humanas **já aprovadas** durante a implantação desta governança;
2. decisões humanas **ainda pendentes**, formalizadas com ID (`P-001`, ...);
3. o que **não** constitui decisão (fatos técnicos, conteúdo de `ROADMAP.md`,
   recomendações de IA);
4. a regra de histórico/supersessão para quando uma decisão aprovada mudar no
   futuro.

Nenhuma pendência humana é resolvida por este documento — ele apenas as
formaliza. Nenhuma decisão aqui listada como "aprovada" foi inventada: cada
uma corresponde a uma determinação humana explícita, dada durante esta
sessão de implantação de governança, ou a um princípio já presente em
`docs/PROJECT_RULES.md` que o humano confirmou ao aprovar `AGENTS.md`.

## B. Regra de interpretação

- **Séries de ID são permanentes e nunca reutilizadas:**
  - `GOV-*` — decisões sobre o processo de governança em si.
  - `SEC-*` — decisões de segurança/controle de ações sensíveis.
  - `OPS-*` — decisões operacionais (execução, isolamento, procedimento).
  - `LEG-*` — decisões jurídicas/processuais do produto.
  - `ARCH-*` — decisões arquiteturais/técnicas estruturais.
  - `PROD-*` — decisões de produto, posicionamento, nomenclatura,
    comercialização ou prioridade de ciclo.
  - `DATA-*` — decisões de privacidade, retenção, descarte e governança de
    dados.
  - `P-*` — pendências humanas ainda não decididas.
- Um item pendente (`P-*`) só se torna decisão aprovada quando um humano o
  decide explicitamente; a partir daí, ganha um novo registro na série
  apropriada conforme sua natureza (`GOV-*`, `SEC-*`, `OPS-*`, `LEG-*`,
  `ARCH-*`, `PROD-*` ou `DATA-*`), referenciando o `P-*` que resolveu — o
  item `P-*` original não é apagado, é marcado como resolvido e referenciado
  (ver Seção G).
- **Nenhum item pendente é considerado resolvido apenas porque um agente de
  IA sugeriu uma opção.** Uma recomendação de IA, quando existir, é marcada
  explicitamente como tal e nunca conta como decisão.
- Este documento não decide nada por si só — apenas registra o que já foi
  decidido e o que ainda não foi.

## C. Decisões de governança aprovadas

- **GOV-001** — Governança documental persistente foi aprovada para uso por
  agentes de IA neste projeto, composta por `AGENTS.md`, `PROJECT_STATE.md`,
  `ROADMAP.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `NEXT_STEP.md` e
  `CLAUDE.md`, na ordem de criação já aprovada (`AGENTS.md` primeiro).
- **GOV-002** — `AGENTS.md` tem precedência sobre as demais regras
  operacionais e de processo deste repositório, conforme a hierarquia
  definida em `AGENTS.md`, Seção 4.
- **GOV-003** — `PROJECT_STATE.md` é tratado como checkpoint documental
  datado, nunca como fonte permanente do estado do Git; branch, HEAD,
  `origin/main` e working tree devem ser reobtidos diretamente via Git em
  cada nova sessão.
- **GOV-004** — `ROADMAP.md` é planejamento; não constitui, por si só,
  autorização automática de execução técnica. Concluir uma etapa não
  autoriza automaticamente iniciar a seguinte.
- **GOV-005** — Cada arquivo de governança é criado individualmente, com
  proposta em texto e aprovação humana explícita antes da escrita em disco,
  nunca em lote.
- **GOV-006** — Evidência objetiva e rastreável pode permanecer válida entre
  sessões quando estiver vinculada a checkpoint/commit conhecido, o código
  relevante não tiver mudado e não houver regressão ou dúvida material que a
  invalide. Memória de agente ou conversa não substitui evidência. Mudança
  relevante exige reexecução dos testes pertinentes conforme `AGENTS.md`,
  Seção 7.
- **GOV-007** — `NEXT_STEP.md` define a única tarefa operacional corrente em
  foco, mas sua existência **não** constitui, por si só, autorização
  automática para execução. Devem ser respeitados `AGENTS.md`, `DECISIONS.md`
  e as autorizações aplicáveis.
- **GOV-008** — Havendo conflito relevante entre Git/código real e
  documentos de governança, o agente deve **PARAR, RELATAR e AGUARDAR**
  orientação humana; nunca corrigir silenciosamente a divergência.

## D. Decisões de segurança/operação aprovadas

- **SEC-001** — Segredos (`.env`, `.env.bak*`, tokens, chaves, senhas) nunca
  são lidos ou expostos por agentes de IA neste repositório; verificações
  futuras de configuração, quando explicitamente autorizadas, limitam-se a
  metadados, nomes de variáveis ou valores não sensíveis/redigidos.
- **SEC-002** — Ações de Git de escrita (`add`/`commit`/`push`/`merge`/
  `tag`/`release`/`deploy`), acesso a Production, migração de banco e
  integrações externas exigem autorização humana explícita e específica
  para cada ato, conforme `AGENTS.md`.
- **OPS-001** — Trabalho não relacionado não deve ser misturado em uma
  working tree que já contenha alterações locais não commitadas de outra
  frente.
- **OPS-002** — A implantação inicial desta governança usa um worktree/
  branch isolado (`chore/governance-docs-v1`), criado a partir do baseline
  Git aprovado (`4e9d22fdae99fc717192ea5b6b96214f61d70628`), preservando
  intacta a branch de trabalho original
  (`fix/editor-civil-professional-risk-specialization-v1`) e os dois
  arquivos locais modificados nela.
- **OPS-003** — Resolve `P-007`. A frente local
  `fix/editor-civil-professional-risk-specialization-v1` (especialização de
  restrição profissional / análise de risco / LGPD; commit original
  `7771de0384d9c9bd56f6ecb62f855674a3d96ed6`) foi validada, integrada a
  `main` via PR #306 (squash-merged; squash commit
  `b9ca8a8141da1a582a0ee2842b9278652e1705f4`) e encerrada. `main` local e
  `origin/main` foram posteriormente sincronizadas nesse mesmo hash. Antes
  da remoção da branch, foi comprovada equivalência material de conteúdo
  entre `main` e a branch remota (`git diff --exit-code` sem diferenças,
  `TREE_EQUIVALENCE_EXIT=0`, nenhum arquivo divergente); a branch local e
  remota `fix/editor-civil-professional-risk-specialization-v1` foram
  removidas somente depois dessa comprovação. O PR #306 permanece
  preservado no histórico do GitHub. Regressão direcionada da frente:
  `108 passed, 0 failed`. Suíte global do backend no momento da validação:
  `304 passed, 2 failed` em 306 testes; as duas falhas (divergência entre
  configuração de limite de plano e expectativa do teste; ambiente
  PostgreSQL local com usuário superuser bypassando RLS e estado
  persistente entre execuções) foram diagnosticadas como externas a esta
  frente, não foram misturadas no PR/commit, e permanecem trabalho
  separado. Production não foi acessada durante o fechamento.

## E. Decisões jurídicas/processuais aprovadas

- **LEG-001** — Revisão e decisão profissional do advogado responsável são
  obrigatórias antes de qualquer protocolo, entrega ao cliente ou uso
  externo relevante de peça, minuta, análise ou relatório gerado com apoio
  de IA.
- **LEG-002** — A IA não inventa fatos, provas, valores, jurisprudência ou
  conclusão jurídica não sustentada pelos dados/evidências disponíveis. A IA
  pode analisar o caso, estruturar alternativas, apontar riscos e apresentar
  recomendações fundamentadas ao advogado, mas **não toma, de forma
  autônoma, a decisão jurídica final**. Dados não confirmados no caso são
  marcados como pendência, nunca presumidos.

## F. Decisões humanas pendentes

Nenhum item desta seção é decidido por este documento. Cada um permanece em
aberto até decisão humana explícita.

- **P-001 — Nomenclatura oficial do produto.** "IA Trabalhista Robusta"
  versus "Plataforma Jurídica Pro". Contexto: ambos os nomes aparecem em
  documentos do projeto (`README.md`/`docs/PRODUTO_OFICIAL.md` vs.
  `docs/legal-coverage-matrix-v1.md`). **Status: pendente.**
- **P-002 — Prioridade do próximo ciclo de desenvolvimento** após esta
  governança. Contexto: `docs/OPERATIONAL_PIPELINE_CHECKPOINT_V1.md` lista 4
  opções (Checklist+WhatsApp, refino visual, documentação comercial,
  exportação do dossiê) sem priorização registrada. **Status: pendente.**
- **P-003 — Eventual refatoração, ou não, de**
  `backend/app/services/case_operational_assistant.py`. Contexto: arquivo de
  ~7.600 linhas, identificado como risco arquitetural em `ARCHITECTURE.md`,
  Seções F e O. **Status: pendente.**
- **P-004 — Fechamento formal do gate de release.** Contexto:
  `RELEASE_CHECKLIST_MVP.md` mantém itens `[ ]` em aberto ("todos os fluxos
  críticos validados", "sem falhas abertas graves"). **Status: pendente.**
- **P-005 — Política formal de retenção/descarte de dados** e demais
  pendências LGPD relevantes. Contexto: `docs/LGPD_MINIMA.md` autodeclara
  essas pendências como abertas. **Status: pendente.**
- **P-006 — Nível de autonomia autorizado para agentes de IA** neste
  projeto (quanto pode ser executado sem aprovação humana passo a passo,
  inclusive quando `NEXT_STEP.md` existir). Esta pendência trata do **nível
  de autonomia operacional que poderá ser concedido dentro das regras
  vigentes** — uma futura decisão sobre autonomia **não deve ser
  interpretada como autorização implícita** para derrubar `SEC-002` ou
  qualquer outra proteção permanente já aprovada. Qualquer alteração futura
  das regras de segurança atualmente aprovadas exige decisão humana
  explícita, novo registro de decisão e aplicação da regra de
  supersessão/histórico (Seção G). **Status: pendente.**
- **P-007 — Destino/fechamento da frente local
  `fix/editor-civil-professional-risk-specialization-v1`**, originalmente
  existente com alterações em `case_operational_assistant.py` e
  `test_massive_multicase_all_blocks_regression.py`. **Status: resolvido em
  `OPS-003`.**
- **P-008 — Tratamento/higiene dos arquivos `.env`/`.env.bak*`** e risco
  operacional relacionado, sem ler ou expor seus conteúdos. **Status:
  pendente.**
- **P-009 — Eventual adoção de storage externo para anexos** (hoje em
  filesystem local por tenant), caso o volume/ambiente venha a justificar.
  **Status: pendente.**
- **P-010 — Necessidade/prioridade de auditoria técnica aprofundada** das
  áreas ainda não auditadas em detalhe: `frontend/`, `modules/jobs`,
  `modules/appeals_reactions`, e o caminho de criação de cobrança via API
  real do Asaas (`ARCHITECTURE.md`, Seções E, K, Q). **Status: pendente.**

## G. Regra de supersessão / histórico

- Nenhuma decisão aprovada (`GOV-*`, `SEC-*`, `OPS-*`, `LEG-*`, `ARCH-*`,
  `PROD-*`, `DATA-*`) é apagada silenciosamente quando muda. Uma mudança
  futura cria um **novo registro** na mesma série (próximo número
  sequencial), com uma nota explícita: *"Supersede [ID anterior]"* — o
  registro anterior permanece no documento, marcado como *"Superseded by
  [novo ID]"*, preservando o histórico completo.
- Quando um item `P-*` é decidido, o próprio item `P-*` permanece registrado
  na Seção F com **Status: resolvido em [ID da decisão correspondente]** —
  não é removido, apenas encerrado com a referência.
- IDs nunca são reaproveitados, mesmo que um item pendente seja descartado
  sem virar decisão formal (nesse caso: **Status: descartado**, com a razão
  registrada).

## H. O que NÃO constitui decisão

- **Estado atual do código ou do Git** — fato técnico observado, registrado
  em `PROJECT_STATE.md`/`ARCHITECTURE.md`, nunca uma decisão por si só.
- **Conteúdo de `ROADMAP.md`** — planejamento, não decisão (`AGENTS.md`,
  Seção 5; `GOV-004` acima).
- **Documentação histórica do projeto** (README, handoffs, matrizes) —
  **não estabelece, por si só, uma decisão humana atual desta governança.**
  Pode servir como evidência de decisão histórica, contexto ou intenção
  anterior, mas qualquer efeito normativo corrente deve ser confirmado pela
  governança atual ou por decisão humana explicitamente registrada. Tem
  precedência menor quando conflitar com a governança atual (`AGENTS.md`,
  Seção 4).
- **Resultados de teste ou achados de auditoria** — evidência objetiva, não
  decisão.
- **Recomendação de um agente de IA** — quando um agente propuser uma opção
  ou sugestão, ela deve ser explicitamente rotulada *"recomendação da IA —
  não é decisão"* e só se torna decisão quando um humano a aprovar
  explicitamente, gerando um novo registro nas Seções C–E. Nenhuma
  recomendação é tratada como aprovada por omissão.

## I. Limites deste documento

- Não decide nenhuma das pendências `P-001` a `P-010`.
- Não autoriza, por si só, implementação, commit, push, deploy, acesso a
  Production ou integração externa — essas ações continuam exigindo
  autorização humana explícita e específica, conforme `AGENTS.md`.
- Não inventa decisão passada sem evidência documental ou aprovação humana
  explícita desta implantação — toda decisão nas Seções C–E corresponde a
  uma determinação humana real ou a um princípio pré-existente em
  `docs/PROJECT_RULES.md` confirmado nesta sessão.
- Não expõe, e não expôs em nenhum momento desta auditoria, conteúdo de
  `.env`/`.env.bak*` ou qualquer segredo.
- Não toca no repositório original nem em Production.
