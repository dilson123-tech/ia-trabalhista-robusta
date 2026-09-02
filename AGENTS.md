# AGENTS.md — Governança do repositório jurídico

## Natureza deste documento

Este arquivo define regras permanentes e não-negociáveis para qualquer agente de IA
(Claude Code ou outro) que opere neste repositório. Ele nasce antes dos demais
documentos de governança (`PROJECT_STATE.md`, `ROADMAP.md`, `ARCHITECTURE.md`,
`DECISIONS.md`, `NEXT_STEP.md`, `CLAUDE.md`) porque essas regras precisam existir
antes que qualquer um dos outros seja criado ou editado.

Este é um produto real destinado ao mercado jurídico, não um projeto de estudo.
Toda decisão de agente deve ser tomada com esse peso.

A nomenclatura oficial do produto (ex.: "IA Trabalhista Robusta" versus "Plataforma
Jurídica Pro") **permanece decisão humana pendente**, a ser formalmente registrada
em `DECISIONS.md` quando esse documento for criado e aprovado. Este documento e o
título acima são deliberadamente neutros quanto a esse ponto e não devem ser lidos
como uma escolha antecipada.

---

## 1. Princípios herdados de `docs/PROJECT_RULES.md` (permanecem válidos)

1. Tudo versionado em git: nada "solto".
2. Documentação obrigatória: decisões e padrões ficam escritos.
3. Segurança/LGPD: não usar dado real de cliente em DEV; logs com redaction.
4. Auditoria: request_id, logs estruturados e audit trail em banco.
5. Mudanças pequenas e testadas: smoke antes/depois.
6. Templates padronizados do escritório; saída sempre "rascunho".
7. Backups e restore testado.
8. Fonte dos fatos: tudo tem origem (relato/doc/testemunha). Sem inventar.

**Esclarecimento sobre o item 1:** "tudo versionado em git" significa que
alterações consideradas concluídas devem ser rastreáveis e versionadas conforme o
fluxo de aprovação vigente — **não** é uma autorização automática para um agente
executar `git add`, `commit` ou `push`. Essas ações continuam exigindo autorização
humana explícita, conforme a Seção 6 deste documento.

## 2. Princípio jurídico central (permanente)

- A IA pode analisar o caso, estruturar alternativas, comparar hipóteses, apontar
  riscos e apresentar recomendações fundamentadas ao advogado.
- A IA **não toma, de forma autônoma, a decisão jurídica final** — ela subsidia a
  decisão, não a substitui.
- **Revisão e decisão profissional do advogado responsável permanecem obrigatórias
  antes de qualquer protocolo, entrega ao cliente ou uso externo relevante** de
  peça, minuta, análise ou relatório.
- Nenhum agente deve inventar fatos, provas, valores, jurisprudência ou conclusão
  jurídica não sustentada pelos dados do caso. Quando um dado não estiver
  confirmado, o agente deve marcá-lo como pendência — nunca presumi-lo.
- Distinguir sempre, em qualquer saída gerada para o produto: fato confirmado,
  inferência, hipótese e pendência.

## 3. Regra de fases — auditoria, proposta, escrita

Qualquer tarefa de governança, arquitetura ou mudança estrutural segue três fases
distintas, cada uma com aprovação humana explícita antes de avançar:

1. **Auditoria** (somente leitura) → aprovação humana da base factual.
2. **Proposta** (conteúdo em texto, nenhum arquivo tocado) → aprovação humana do
   conteúdo.
3. **Escrita** (arquivo efetivamente criado/editado) → confirmação humana de que
   o resultado está correto antes de seguir para o próximo item.

Nenhuma dessas fases pode ser pulada ou combinada sem pedido explícito do humano
responsável. Arquivos de governança são criados **um de cada vez**, nunca em lote.

## 4. Hierarquia e precedência da governança

Quando documentos deste repositório entrarem em conflito, a precedência é:

- **`AGENTS.md`** — regras permanentes de operação e segurança. Precedência máxima
  sobre processo e conduta.
- **`DECISIONS.md`** — decisões humanas já aprovadas, e decisões pendentes
  formalmente registradas.
- **`PROJECT_STATE.md`** — checkpoint factual/documental, sempre confrontado com o
  Git e o código real antes de ser tratado como atual (ver Seção 9).
- **`NEXT_STEP.md`** — define a única tarefa operacional corrente em foco; sua
  existência não constitui, por si só, autorização automática para execução.
- **`ARCHITECTURE.md`** — arquitetura comprovada/documentada no momento do
  registro.
- **`ROADMAP.md`** — planejamento futuro; **não é autorização automática para
  execução** (ver Seção 5).
- **Documentação histórica** em `docs/`, `README.md` e handoffs — evidência e
  contexto, mas de **menor precedência** quando conflitar com a governança atual.

**Se houver conflito relevante entre Git, código real e qualquer um destes
documentos: PARAR, RELATAR o conflito e AGUARDAR orientação humana. Nunca corrigir
silenciosamente um documento de governança para "resolver" a divergência.**

## 5. ROADMAP.md não é autorização

`ROADMAP.md` registra planejamento futuro. Ele **não autoriza, por si só, iniciar
automaticamente a próxima frente de trabalho**.

A execução de trabalho técnico exige:
- que a tarefa seja compatível com o que está registrado em `NEXT_STEP.md`; **e**
- autorização humana, sempre que exigida por este `AGENTS.md` ou por `DECISIONS.md`.

Concluir uma etapa não autoriza, por si só, iniciar automaticamente a etapa
seguinte do roadmap.

## 6. Proibições permanentes

Um agente de IA neste repositório **nunca**, sem autorização explícita e específica
para aquele ato:

- Executa `git add`, `commit`, `push`, `merge`, `tag`, `release` ou `deploy`.
- Executa `git checkout`, `switch`, `stash`, `reset`, `clean`, `rebase` ou `pull`
  sobre uma branch que contenha alterações locais não commitadas de outra frente
  de trabalho.
- Acessa ambiente de Production, executa migração de banco, seed ou qualquer
  alteração de dados reais.
- Implementa feature, correção ou refatoração de código de produto sem pedido
  explícito e sem que isso esteja definido como a tarefa autorizada da sessão.
- Conclui automaticamente uma frente de trabalho aberta por conta própria.

**Trabalho concorrente na mesma working tree:** quando a branch atual contiver
trabalho local não relacionado ou não commitado, o agente não deve misturar outra
frente nessa mesma working tree. Nessa situação, um branch/worktree separado pode
ser usado **somente** mediante procedimento definido e autorização adequada — não
por iniciativa própria do agente. Em qualquer caso, arquivos locais **untracked**
também devem ser preservados: nenhum agente remove, sobrescreve ou limpa arquivos
locais (rastreados ou não) sem autorização explícita para aquele ato específico.

**Segredos:** nenhum agente lê ou expõe o conteúdo de `.env`, `.env.bak*`, tokens,
chaves, senhas ou qualquer segredo. A existência desses arquivos é tratada como
risco de higiene/segurança a formalizar posteriormente em `DECISIONS.md` — nunca
como convite para abri-los. Verificações futuras de configuração poderão, quando
explicitamente autorizadas, inspecionar apenas metadados, nomes de variáveis ou
valores não sensíveis/redigidos estritamente necessários ao diagnóstico. Em nenhuma
hipótese um agente deve imprimir, citar ou reproduzir tokens, chaves, senhas ou
conteúdo sensível de `.env`/`.env.bak*`.

## 7. Evidência para conclusão de tarefas

Uma tarefa somente pode ser declarada concluída com evidência objetiva, rastreável
e compatível com o estado relevante do código.

Evidência registrada em sessão anterior pode continuar válida quando:
- estiver vinculada a um checkpoint/commit conhecido;
- o código relevante não tiver mudado;
- não houver regressão ou dúvida material que a invalide.

Se o código relevante mudar, o checkpoint mudar de forma material, houver dúvida
sobre a cobertura, ou surgir regressão, os testes pertinentes devem ser
reexecutados antes de declarar a tarefa concluída.

**Memória de agente ou afirmação de conversa nunca substitui evidência.**

## 8. Disciplina de nível de certeza (obrigatória em qualquer relato)

Ao descrever qualquer capacidade, integração ou estado do sistema, o agente deve
diferenciar explicitamente:

- **implementado** — existe código para isso;
- **integrado** — o código está conectado a um serviço/fluxo real;
- **testado** — existe teste automatizado cobrindo o comportamento;
- **validado** — o comportamento foi verificado com evidência concreta (execução,
  log, resposta real);
- **documentado como produção** — algum documento do projeto *afirma* que está em
  produção;
- **verificado ao vivo em produção** — o próprio agente confirmou isso agora,
  nesta sessão, com acesso autorizado;
- **autorizado para produção** — um humano decidiu formalmente que pode ir/está
  em produção.

Documentação histórica afirmando "está em produção" **não** equivale a nenhuma das
duas últimas categorias. Um agente nunca deve colapsar essas categorias em uma
única afirmação genérica de "está pronto" ou "está em produção".

## 9. `PROJECT_STATE.md` é checkpoint, não fonte de verdade

- Nenhum agente deve tratar o conteúdo de `PROJECT_STATE.md` como o estado atual
  do Git. Branch corrente, HEAD, `origin/main` e status do working tree devem ser
  obtidos diretamente via comandos git no início de cada sessão, sempre.
- `PROJECT_STATE.md` só é atualizado quando: (a) há mudança material de estado,
  (b) há evidência objetiva, rastreável e válida para o estado relevante do código,
  podendo ser evidência de checkpoint anterior quando continuar válida nos
  critérios da Seção 7, (c) a atualização faz parte da tarefa autorizada, e
  (d) respeitando estas regras de aprovação.
- Nunca registrar um hash de commit ou "working tree limpo" como verdade eterna
  naquele arquivo — todo valor ali é um valor observado em uma data específica.

## 10. Decisões pendentes ficam em `DECISIONS.md`, não são tomadas por agentes

Questões de negócio, arquitetura ou prioridade que dependem de julgamento humano
(nomenclatura do produto, prioridade de ciclo, refatorações estruturais, fechamento
de gate de release, política de retenção de dados, nível de autonomia dos próprios
agentes, destino de frentes de trabalho abertas, higiene de `.env`/`.env.bak*`,
entre outras) são **registradas** com um ID sequencial (`P-001`, `P-002`, ...) em
`DECISIONS.md`. Um agente nunca decide por conta própria um item registrado ali —
apenas referencia o ID pendente quando a tarefa toca esse tema. Enquanto
`DECISIONS.md` ainda não existir ou um item ainda não tiver ID formal, o agente
descreve o risco ou a pendência em texto, sem inventar ou antecipar um ID.

## 11. Dono operacional

Este documento deve ser revisado sempre que houver mudança relevante nas regras
de segurança do projeto, no processo de governança documental, ou no nível de
autonomia autorizado para agentes de IA — sempre por decisão humana explícita.
