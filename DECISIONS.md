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
  `304 passed, 2 failed` em 306 testes; as duas falhas
  (`test_admin_tenant_usage_full_returns_consolidated_view` e
  `test_rls_isolation`) foram diagnosticadas como externas a esta frente,
  não foram misturadas no PR/commit, e permanecem trabalho separado. O
  diagnóstico inicial dessas falhas registrado à época (superuser local
  "bypassando RLS") foi **superado** pela auditoria-mestra de 2026-09-24 —
  ver `OPS-004`. Production não foi acessada durante o fechamento.
- **OPS-004** — Resolve `P-002` **somente como prioridade**. Decisão
  humana: **a próxima PRIORIDADE do projeto é restaurar uma baseline
  confiável de testes e isolamento multi-tenant antes de novas features.**
  Esta decisão define apenas a prioridade; ela **não** define a solução
  técnica das duas falhas conhecidas da suíte global do backend
  (`304 passed, 2 failed` em 306 testes, último resultado conhecido
  registrado em `OPS-003`, não reexecutado nesta decisão).
  Base factual (auditoria-mestra somente leitura de 2026-09-24, sobre o
  HEAD `0fc0755d7de4ced50400f6e297a99338f6d9cd50`):
  - `test_rls_isolation`: **não** se atribui a falha apenas a um role
    PostgreSQL superusuário. A auditoria **não encontrou** nas migrations
    versionadas `ENABLE ROW LEVEL SECURITY` nem `CREATE POLICY`;
    `set_config('app.tenant_id', ...)` existe em `backend/app/core/tenant.py`,
    mas nada versionado o consome. RLS **não está comprovado no Git**. O
    isolamento hoje observado no código é em nível de aplicação
    (`scoped_query`). O teste usa o PostgreSQL local real e grava dados
    (suíte não hermética). O estado do banco local e o estado de Production
    **não foram verificados**.
  - `test_admin_tenant_usage_full_returns_consolidated_view`: o teste espera
    `case_limit == 50`, enquanto a rota administrativa deriva o limite de
    `limits_for(get_effective_plan().plan_type)`. Não é uma simples troca
    de número fixo por configuração: há uma questão de semântica do limite
    exibido ao admin, pendente de decisão humana (item B abaixo) à época
    desta decisão — decidida posteriormente em `ARCH-002`.
  A execução técnica desta prioridade depende de **duas decisões humanas**,
  pendentes à época e que esta decisão **não** toma (ambas decididas
  posteriormente, em 2026-09-25, por registros próprios — `ARCH-001` e
  `ARCH-002`):
  - **A — Modelo de isolamento multi-tenant:** (A1) implementar RLS
    PostgreSQL real e versionado; **ou** (A2) assumir formalmente
    isolamento somente em nível de aplicação e ajustar arquitetura, testes
    e documentação a esse modelo. **Status: decidida (humana) em
    2026-09-25 — A1, registrada em `ARCH-001`.**
  - **B — Semântica do limite exibido na visão administrativa:** (B1)
    `Subscription.case_limit`; **ou** (B2) limite derivado de
    `limits_for(plan_type)`. **Status: decidida (humana) em 2026-09-25 —
    B2, registrada em `ARCH-002`.**
  O nome `fix/ci-plan-limit-test-and-rls-role-isolation-v1`, proposto
  anteriormente, foi **superado** pela auditoria-mestra: essa branch
  **nunca foi criada** e **não** constitui frente autorizada. Esta decisão
  **não autoriza automaticamente**: criação de branch técnica, início de
  implementação, alteração de testes ou código, alteração de banco/role,
  migrations, execução de `pytest`, acesso a Production, decisão comercial
  sobre valores de limites de plano, escolha de A ou B, ou resolução de
  qualquer outra pendência (`P-001`, `P-003` a `P-006`, `P-008` a `P-010`),
  que permanecem pendentes e intactas.
- **OPS-005** — Modelo de execução da prioridade de `OPS-004` com as
  decisões `ARCH-001` (A1) e `ARCH-002` (B2): **sequência obrigatória
  BLOCO 1A → BLOCO 2 → BLOCO 1B** ("Modelo Y" com refinamento). Decisão
  humana (DICO/ChatGPT), 2026-09-25, tomada após relatório somente leitura
  de preparação do BLOCO 1 sobre o HEAD
  `ba169bcaadb9836dd9763f96ba818a7544d37ea8`.
  - **BLOCO 1A — hermeticidade/configuração de testes:**
    - PostgreSQL **16** efêmero para testes;
    - migrations aplicadas no banco de teste;
    - eliminar a dependência do `.env` real e do PostgreSQL de
      desenvolvimento;
    - reconciliar `test_admin_tenant_usage_full_returns_consolidated_view`
      com `ARCH-002` (B2);
    - adaptar a infraestrutura de `test_rls_isolation` ao PostgreSQL
      efêmero, **preservando seu assert**, deixando explícito que ele
      ainda depende do BLOCO 2 para ficar verde;
    - **nenhum** `skip`, **nenhum** `xfail`, **nenhum** assert
      enfraquecido;
    - `remaining.cases` permanece inalterado.
  - **BLOCO 2 — implementar `ARCH-001` (A1):** RLS real e versionado; role
    de aplicação não superusuária, sem `BYPASSRLS`; ownership/`FORCE ROW
    LEVEL SECURITY` tratado explicitamente; isolamento em PostgreSQL real;
    `test_rls_isolation` deve ficar verde.
  - **BLOCO 1B — somente depois do BLOCO 2:** adicionar/fechar a suíte
    completa do backend no CI; CI completo obrigatório e verde; executar e
    registrar a baseline final. **Nenhum BLOCO 1 será declarado concluído
    antes do 1B.**
  - **Refinamento obrigatório:** **não** adicionar no BLOCO 1A um job de
    suíte completa propositalmente vermelho, nem mesmo como não-required.
    O job completo entra somente no BLOCO 1B, depois do RLS, para não
    normalizar checks vermelhos.
  - **Decisões técnicas adicionais:**
    - PostgreSQL de testes = versão 16, por alinhamento ao
      `docker-compose.yml` versionado; isso **não** afirma a versão de
      Production (não verificada);
    - tentar primeiro bootstrap precoce de configuração pelo `conftest.py`;
    - `settings.py` só poderá receber hook mínimo de teste se
      objetivamente necessário para impedir contaminação pelo `.env` real,
      sem alterar defaults nem comportamento de produção;
    - `remaining.cases` / `cases_per_month` ficam **congelados** nesta
      frente (1A → 2 → 1B) e exigem decisão humana própria futura antes de
      qualquer mudança de contrato (ver achado em `ARCH-002`).
  Esta decisão define **ordem e critérios**; ela **não implementa nada** e
  **não autoriza automaticamente**: criação de branch, alteração de
  código, testes, CI/workflow, banco/role ou migrations, execução de
  `pytest`/build, acesso a Production ou qualquer ato de Git de escrita —
  cada ato de cada bloco continua exigindo autorização humana específica.
  Concluir um bloco não autoriza iniciar o seguinte por inferência.

### Decisões arquiteturais aprovadas (série `ARCH-*`)

- **ARCH-001** — Resolve o item **A** de `OPS-004` (modelo de isolamento
  multi-tenant). Decisão humana (DICO/ChatGPT), 2026-09-25: **opção A1 —
  implementar RLS PostgreSQL real e versionado, mantendo também o
  isolamento multi-tenant em nível de aplicação.** Requisitos obrigatórios
  da implementação futura:
  - policies de RLS versionadas por migration;
  - role de aplicação apropriada, **não superusuária**, sem atributo
    `BYPASSRLS` e sem depender da propriedade das tabelas protegidas para
    isolamento; a implementação deve tratar explicitamente a relação entre
    ownership e `FORCE ROW LEVEL SECURITY`;
  - isolamento testado em PostgreSQL real;
  - cobertura em CI;
  - `scoped_query`/isolamento de aplicação mantido como camada adicional
    (defesa em profundidade), não substituído pelo RLS.
  Evidência de base (auditoria-mestra de 2026-09-24, registrada em
  `OPS-004`): não há `ENABLE ROW LEVEL SECURITY` nem `CREATE POLICY` nas
  migrations versionadas; `set_config('app.tenant_id', ...)` em
  `backend/app/core/tenant.py` não tem consumidor versionado; o isolamento
  hoje observado é em nível de aplicação (`scoped_query`). Estado do banco
  local e de Production **não verificados**.
  **Esta decisão não implementa RLS** e **não autoriza automaticamente**:
  criação de branch, migration, alteração de role/banco, alteração de
  código ou testes, execução de `pytest`, alteração de CI ou acesso a
  Production — cada ato continua exigindo autorização humana específica.
- **ARCH-002** — Resolve o item **B** de `OPS-004` (semântica do limite
  administrativo). Decisão humana (DICO/ChatGPT), 2026-09-25: **opção B2 —
  `limits_for(plan_type)` é a FONTE OFICIAL da verdade para limites de
  plano e para enforcement.** Fundamentos (investigação somente leitura de
  2026-09-25, sobre o HEAD `55945775ffeda2a8ea5c033bd8569d156f0972ac`):
  - o enforcement (`backend/app/services/plan_enforcement.py`) usa
    `limits_for(get_effective_plan().plan_type)`;
  - o resumo de uso (`usage_summary`) usa `limits_for`;
  - o frontend consome `usage/summary-v2`, baseado em `limits_for`;
  - a documentação comercial descreve limites **por plano**;
  - não existe fluxo de override contratual de `case_limit` (o schema de
    upsert administrativo não expõe o campo);
  - os writers de `Subscription.case_limit` (signup, webhook, rotas admin)
    apenas copiam o limite do plano (`limits_for(plan).cases_per_month`);
  - `case_limit` não participa do enforcement (as funções legadas de
    `backend/app/core/subscription.py` que o consultariam não têm
    chamadores).
  Consequências aprovadas:
  1. `Subscription.case_limit` passa a ser tratado como campo
     **LEGADO/INFORMATIVO** no estado atual.
  2. `case_limit` **não** é fonte de enforcement, **não** é override
     contratual e **não** é a fonte oficial do limite administrativo.
  3. A coluna **não** é removida. Qualquer remoção ou deprecação futura
     exige análise separada e nova decisão humana.
  4. `test_admin_tenant_usage_full_returns_consolidated_view` deverá ser
     futuramente reconciliado com B2, **sem** depender de valor `50`
     hardcoded e **sem** depender do `.env` local.
  Esta decisão **não** altera código, testes, banco ou valores comerciais
  de limites, e **não autoriza automaticamente** a implementação dessas
  consequências.
  **Achado técnico independente registrado (não decidido, sem solução
  definida):** `cases_per_month` é alias legado de `active_cases_limit`,
  mas `remaining.cases` é calculado contra o contador mensal
  `cases_created` (rota administrativa de uso consolidado, `/summary-v2` e
  resumo/exportação administrativa de uso). Isso mistura o limite de casos
  **ATIVOS** com o contador de casos **CRIADOS NO MÊS**. Registrado como
  problema técnico a tratar no **BLOCO 1**; a correção (semântica e
  implementação) permanece pendente de análise e decisão humana
  específicas. **Atualização (`OPS-005`, 2026-09-25):** esse achado
  **não** será corrigido na frente 1A → 2 → 1B; `remaining.cases` /
  `cases_per_month` ficam congelados até decisão humana própria futura.


- **OPS-006** — Resolve `P-006`. Fica aprovada a autonomia operacional
  supervisionada dos agentes de IA. Após DICO autorizar explicitamente uma
  missão com escopo e critérios definidos, os agentes podem, sem nova
  aprovação humana passo a passo, investigar o código, editar somente dentro
  do escopo autorizado, executar testes locais permitidos, analisar falhas,
  aplicar correções diretamente relacionadas, repetir testes e realizar
  revisão adversarial até concluir, bloquear ou atingir o limite da missão.
  A autonomia não autoriza expansão de escopo, resolução autônoma de decisão
  humana pendente, mudança arquitetural não prevista, enfraquecimento de
  testes, regras jurídicas ou segurança, leitura de segredos ou descarte de
  alterações inesperadas. Dúvida material, conflito de governança ou
  necessidade de ampliar o escopo exige parada e escalonamento. `SEC-001` e
  `SEC-002` permanecem integralmente válidas; portanto `git add`, `commit`,
  `push`, `merge`, `tag`, `release`, `deploy`, acesso a Production, migrations
  e integrações externas continuam exigindo autorização humana explícita e
  específica para cada ato. O executor não aprova sua própria entrega. A
  missão deve terminar com evidências de testes, regressão pertinente, QA
  adversarial, estado Git, riscos, itens não validados e resultado
  `CONCLUÍDA`, `PARCIAL` ou `BLOQUEADA`. A frase operacional
  `AUTORIZADO — EXECUTEM` inicia essa autonomia somente quando vinculada a
  uma missão previamente definida e aprovada; isoladamente não concede
  autorização genérica sobre o repositório. Decisão humana (DICO/ChatGPT),
  2026-09-30.

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
  exportação do dossiê) sem priorização registrada. **Status: resolvido em
  `OPS-004` apenas como prioridade** (baseline confiável de testes e
  isolamento multi-tenant antes de novas features); as decisões técnicas
  A (modelo de isolamento) e B (semântica do limite admin) descritas em
  `OPS-004` foram decididas por humano em 2026-09-25: A1 em `ARCH-001` e
  B2 em `ARCH-002`.
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
  supersessão/histórico (Seção G). **Status: resolvido em `OPS-006`.**
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

- Não decide, por iniciativa própria, nenhuma das pendências `P-001` a
  `P-010`; os itens marcados como resolvidos (`P-002`, `P-007`) e as
  decisões `A`/`B` de `OPS-004` (`ARCH-001`/`ARCH-002`) e o modelo de
  execução `OPS-005` apenas registram decisões humanas explícitas.
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
