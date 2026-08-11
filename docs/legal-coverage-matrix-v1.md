# Matriz de Cobertura Jurídica V1

## Plataforma Jurídica Pro

**Fase oficial:** Matriz de Cobertura Jurídica
**Base técnica:** estado posterior à `v0.2.34-editor-all-blocks-consumer-universal-action-scope-router-v1`
**Natureza:** documento oficial de cobertura, priorização e controle de evolução jurídica

---

## 1. Finalidade

Este documento passa a ser o mapa oficial de cobertura jurídica da Plataforma Jurídica Pro.

Sua função é registrar, de forma verificável:

- as áreas jurídicas reconhecidas pela plataforma;
- os principais tipos de ação ou medida;
- o nível atual de especialização;
- as entregas que sustentam cada cobertura;
- as lacunas ainda existentes;
- a próxima evolução necessária para cada item.

A matriz não mede apenas se a plataforma consegue produzir algum texto.

Ela mede se existe cobertura jurídica específica, prudente, coerente e protegida contra regressões.

---

## 2. Natureza permanente do produto

A Plataforma Jurídica Pro não é um gerador automático de petições.

Ela é um assistente jurídico profissional destinado à produção de minutas preliminares:

- organizadas;
- prudentes;
- coerentes;
- revisáveis;
- vinculadas aos fatos relatados;
- vinculadas aos documentos disponíveis;
- sujeitas à decisão final do advogado responsável.

A plataforma não deve:

- inventar fatos;
- inventar documentos;
- inventar pedidos;
- inventar provas;
- presumir competência;
- presumir rito;
- presumir urgência;
- presumir tese jurídica;
- prometer resultado;
- substituir análise profissional;
- produzir peça tratada como pronta para protocolo sem revisão.

Quando houver dúvida entre aumentar o conteúdo e preservar a precisão, a precisão prevalece.

---

## 3. Trilhas de cobertura

A plataforma possui capacidades diferentes que não devem ser confundidas.

### 3.1 Cobertura operacional

Inclui recursos como:

- cadastro e organização do caso;
- audiência estratégica;
- análise assistida;
- checklists;
- anexos e provas;
- documentos editáveis;
- exportação;
- fluxos QA históricos.

Uma área pode possuir cobertura operacional e ainda não possuir especialização completa no Editor de minutas.

### 3.2 Cobertura do Editor de minutas

Mede se o Editor consegue produzir os sete blocos com especialização compatível com o tipo de ação:

1. endereçamento;
2. qualificação das partes;
3. resumo fático;
4. fundamentação preliminar;
5. pedidos;
6. provas e requerimentos;
7. fechamento e conferência final.

### 3.3 Cobertura jurídica completa

Um item somente pode ser tratado como completamente pronto quando possuir, de forma compatível:

- detecção do tipo de ação;
- fundamentação específica;
- pedidos específicos;
- provas específicas;
- cautelas permanentes;
- testes automatizados;
- regressão completa;
- teste real no navegador;
- merge;
- tag;
- registro atualizado nesta matriz.

A validação de uma audiência estratégica, checklist ou PDF não transforma automaticamente o Editor em especializado.

---

## 4. Classificação oficial

### ✅ PRONTO

Cobertura específica validada para uso supervisionado.

Critérios esperados:

- tipo de ação detectado;
- blocos essenciais especializados;
- fundamentação compatível;
- pedidos compatíveis;
- provas compatíveis;
- cautelas preservadas;
- testes automatizados;
- regressão aprovada;
- teste real documentado quando aplicável;
- merge e tag oficiais.

O status pronto não elimina a revisão obrigatória do advogado.

### 🟡 PARCIAL

Existe cobertura aproveitável, mas ainda incompleta.

Pode ocorrer quando:

- existe checklist ou fluxo operacional;
- existe roteamento de fundamentação e pedidos;
- apenas alguns blocos estão especializados;
- o bloco de provas ainda é genérico;
- o endereçamento ou a qualificação ainda são genéricos;
- existem marcadores, mas não testes dedicados;
- existe validação antiga fora do Editor;
- o caso depende de revisão técnica reforçada.

Itens parciais não devem ser apresentados como especialização completa.

### 🔴 INEXISTENTE

Não existe cobertura específica suficiente para tratar o item como funcionalmente mapeado.

Pode existir fallback prudente, mas isso não equivale a especialização jurídica.

O item deve passar pelo ciclo completo antes de ser apresentado como pronto.

---

## 5. Hierarquia das evidências

A classificação deve considerar, nesta ordem:

1. implementação atual do Editor;
2. testes automatizados atuais;
3. teste real no navegador;
4. tag oficial;
5. relatórios QA;
6. checklists documentados;
7. fluxos operacionais históricos;
8. fallback genérico.

Documentação antiga não pode superar o comportamento real do código atual.

---

## 6. Cobertura transversal do Editor

| Capacidade transversal | Status | Evidência principal | Pendência |
|---|---:|---|---|
| Geração dos sete blocos oficiais | ✅ | Suíte estrutural da série `v0.2.22` a `v0.2.24` | Preservar em toda regressão |
| Separação entre blocos | ✅ | Regressão estrutural e golden fixture | Não permitir contaminação entre blocos |
| Sincronização do prompt do frontend | ✅ | `v0.2.24-editor-all-blocks-frontend-prompt-golden-sync-v1` | Manter contrato sincronizado |
| Roteador universal de especialização | ✅ | `v0.2.26-editor-all-blocks-universal-action-specialization-router-v1` | Ampliar somente por itens da matriz |
| Cautela sobre fatos e documentos | ✅ | Regras permanentes do Editor | Não remover |
| Cautela sobre competência e rito | ✅ | Regras permanentes do Editor | Não assumir automaticamente |
| Cautela sobre pedidos finais | ✅ | Fechamento e limites do bloco de pedidos | Não transformar sugestão em decisão final |
| Fallback genérico prudente | ✅ | `generic_prudent` | Não confundir fallback com cobertura específica |
| Provas específicas para todas as ações | 🟡 | Família, risco laboral e escopos consumeristas prioritários possuem especialização | Horas, Cível e demais áreas ainda usam base genérica em parte |
| Endereçamento específico para todas as áreas | 🟡 | Família, Trabalhista especializado e Consumidor possuem tratamento próprio | Cível, Previdenciário, Criminal e Ambiental pendentes |
| Qualificação específica para todas as áreas | 🟡 | Família, Trabalhista especializado e Consumidor possuem tratamento próprio | Cível, Previdenciário, Criminal e Ambiental pendentes |
| Teste real por tipo de ação | 🟡 | Consumidor possui validação real nos nove escopos prioritários, nas três rotas bancárias isoladas e no cenário bancário combinado; Família e risco laboral também possuem evidências próprias | Completar subtipos consumeristas e demais áreas conforme expansão |

---

## 7. Matriz por área jurídica

### 7.1 Trabalhista

#### Estado geral

Área madura, com especialização relevante no Editor.

A maturidade não é uniforme entre todos os tipos de ação.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Endereçamento e qualificação trabalhista | ✅ | ✅ | ✅ | `v0.2.30` | Ampliar somente quando novos tipos exigirem partes diferentes |
| Horas extras | ✅ | 🟡 | 🟡 | `v0.2.27` | Criar provas específicas e teste real próprio |
| Intervalo intrajornada | ✅ | 🟡 | 🟡 | `v0.2.27` | Criar provas específicas e teste real próprio |
| Divergência de controles de jornada | ✅ | 🟡 | 🟡 | `v0.2.27` | Especializar bloco probatório |
| Insalubridade por calor ou ambiente de fusão | ✅ | ✅ | ✅ | `v0.2.28`, `v0.2.29`, `v0.2.30` | Preservar regressão e ampliar com novos agentes somente por caso real |
| Periculosidade vinculada a risco técnico comprovável | ✅ | 🟡 | 🟡 | `v0.2.28`, `v0.2.29` | A rota atual trata a periculosidade com cautela e de forma subsidiária; faltam cenários próprios |
| PPP, LTCAT, PGR, PCMSO e EPI | ✅ | ✅ | ✅ | `v0.2.29` | Preservar a especificidade técnica |
| FGTS como reflexo ou documento | ✅ | 🟡 | 🟡 | Cobertura transversal nos fluxos trabalhistas | Criar ação própria quando FGTS for o núcleo do caso |
| Verbas rescisórias | ✅ | 🟡 | 🟡 | Checklist trabalhista e fallback | Criar detecção, fundamentação, pedidos e provas específicos |
| Reconhecimento de vínculo | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Anotação ou retificação de CTPS | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Rescisão indireta | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Dano moral trabalhista | ✅ | 🟡 | 🟡 | Checklist e cautelas gerais | Criar critérios específicos de conduta, nexo e prova |
| Atraso salarial | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Acúmulo ou desvio de função | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Equiparação salarial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar caso real e ciclo completo |
| Acidente de trabalho | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar rota com prova médica, técnica e nexo causal |
| Doença ocupacional | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar rota com documentos médicos e ocupacionais |
| Assédio moral ou sexual | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar tratamento sensível, probatório e cauteloso |
| Estabilidade provisória | 🔴 | 🔴 | 🔴 | Sem entrega específica | Mapear gestante, acidentária, sindical e demais hipóteses |
| Trabalho sem registro com múltiplos pedidos | 🟡 | 🔴 | 🟡 | Base geral trabalhista | Criar combinação controlada de vínculo, CTPS, verbas e FGTS |

#### Próximos pacotes recomendados

1. Completar provas específicas de horas extras e intervalo.
2. Criar especialização de acidente/doença ocupacional como pacote único.
3. Criar especialização de vínculo, CTPS, verbas e FGTS como família coerente.
4. Criar rescisão indireta somente após caso real e prova mínima.
5. Tratar assédio e estabilidade como pacotes sensíveis separados.

---

### 7.2 Família

#### Estado geral

Área muito madura para alimentos, guarda e convivência.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Alimentos | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo e impedir mistura com guarda ou visitas |
| Guarda | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo isolado |
| Convivência | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo isolado |
| Regulamentação de visitas | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo isolado |
| Alimentos + guarda | ✅ | ✅ | ✅ | Série `v0.2.31` a `v0.2.33` | Manter combinação somente quando os dois temas existirem |
| Guarda + convivência | ✅ | ✅ | ✅ | Série `v0.2.31` a `v0.2.33` | Manter combinação somente quando os dois temas existirem |
| Alimentos + guarda + convivência | ✅ | ✅ | ✅ | Série `v0.2.31` a `v0.2.33` | Preservar pedidos compatíveis |
| Provas familiares | ✅ | ✅ | ✅ | `v0.2.32` | Preservar certidões, renda, despesas, escola, saúde e rotina |
| Revisão de alimentos | ✅ | 🟡 | 🟡 | Marcadores existentes e checklist | Criar teste específico e ajustar pedidos próprios |
| Exoneração de alimentos | ✅ | 🟡 | 🟡 | Marcadores existentes e checklist | Criar teste específico e evitar pedido genérico de fixação |
| Divórcio consensual | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização do Editor |
| Divórcio litigioso | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização do Editor |
| Reconhecimento ou dissolução de união estável | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização do Editor |
| Partilha de bens | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização patrimonial e documental |
| Cumprimento de acordo ou decisão familiar | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização processual própria |
| Investigação de paternidade | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar ciclo completo com prova genética e cautelas |
| Adoção | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo sensível próprio |
| Curatela | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige tratamento de capacidade e prova médica |
| Tutela | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo sensível próprio |
| Alienação parental | 🟡 | 🔴 | 🔴 | Apenas cautela documental | Não criar acusação automática; exige base técnica e caso real |

#### Próximos pacotes recomendados

1. Separar revisão e exoneração de alimentos.
2. Criar pacote divórcio e união estável.
3. Criar pacote patrimonial de partilha.
4. Tratar investigação de paternidade, adoção, curatela e tutela somente como módulos sensíveis completos.

---

### 7.3 Consumidor

#### Estado geral

A `v0.2.34` criou o roteador universal de escopos consumeristas.

A `v0.2.36` especializou o Bloco 6 — Provas e requerimentos para fraude bancária/Pix, cobrança indevida, negativação, produto, serviço, plano de saúde, veículo e contrato consumerista geral.

A `v0.2.37` especializou o Bloco 1 — Endereçamento e o Bloco 2 — Qualificação das partes para as rotas consumeristas universais e de veículo, preservando dados reais informados e mantendo competência, rito, partes e documentos sob confirmação profissional.

A `v0.2.38` validou em navegador produto defeituoso ou com vício, serviço defeituoso ou incompleto, plano de saúde, veículo e contrato consumerista geral. A entrega também endureceu a detecção para não inferir danos, urgência, procedimentos médicos, medidas jurídicas ou provas não informadas no caso.

A `v0.2.39` validou em navegador, de forma isolada, fraude bancária ou Pix não reconhecido, cobrança indevida e negativação indevida. A entrega tornou condicionais os pedidos, fundamentos e provas dessas rotas, impedindo a presunção de cobranças futuras, boletim de ocorrência, contratos, autorizações, histórico de débitos, comunicação prévia, efeitos da restrição ou outros elementos não informados.

A `v0.2.40` separou serviço não prestado da rota de serviço defeituoso ou incompleto e validou em navegador os cenários completo e mínimo. A entrega passou a tratar a ausência total de execução sem presumir refazimento, correção, execução parcial, tentativas de reparo ou documentos não informados, condicionando a restituição à existência de pagamento relatado.

A `v0.2.41` separou descumprimento de oferta ou publicidade do contrato consumerista geral e validou em navegador os cenários completo e mínimo. A entrega passou a examinar o conteúdo anunciado e a conduta do fornecedor sem presumir pedido, pagamento, protocolos, mensagens, cancelamento, reembolso, não entrega, rastreamento, danos ou outros elementos não informados.

A `v0.2.42` separou cancelamento solicitado e não efetivado do contrato consumerista geral e validou em navegador os cenários completo e mínimo. A entrega passou a tratar fundamentação, pedidos e provas de forma específica e condicional, sem presumir contrato, protocolo, mensagens, faturas posteriores, pagamentos, cobranças posteriores, restituição, danos ou outros elementos não informados.

A `v0.2.43` separou atraso ou falha de entrega do contrato consumerista geral e validou em navegador os cenários completo e mínimo. A entrega passou a tratar prazo vencido e pedido não entregue com fundamentação, pedido e provas específicos, sem presumir registro do pedido, pagamento, comprovante de prazo, rastreamento, protocolos, mensagens, tentativa de entrega, entrega parcial, cancelamento, reembolso, danos, datas, valores ou outros elementos não informados.

A `v0.2.44` separou falha de garantia da rota geral de produto defeituoso ou com vício e validou em navegador os cenários completo e mínimo. A entrega passou a tratar o acionamento da garantia, a atuação do fornecedor e a solução efetiva do defeito com fundamentação, pedido e provas condicionais, sem presumir nota fiscal, certificado de garantia, ordem de serviço, assistência técnica, tentativa de reparo, protocolos, mensagens, fotografias, vídeos, laudo técnico, substituição, restituição, abatimento, danos, urgência, datas, valores ou outros elementos não informados.

A `v0.2.45` criou especialização própria para falha em serviços de telecomunicações, separada da rota genérica de serviço defeituoso. A entrega passou a tratar contrato ou plano, faturas, protocolos, mensagens, registros de falha ou interrupção, testes de velocidade, suporte técnico e portabilidade somente quando efetivamente informados, com fundamentação, pedido e provas condicionais. Os cenários completo e mínimo foram validados em navegador sem presumir documentos, cancelamento, restituição, danos, urgência, datas, valores ou providências não relatadas.

A `v0.2.46` criou especialização própria para falha no fornecimento de energia elétrica, separada das rotas genéricas de serviço defeituoso e serviço não prestado. A entrega passou a tratar unidade consumidora, faturas, protocolos, mensagens, registros de interrupção, medidor, vistoria técnica, aviso de corte e religação somente quando efetivamente informados, com fundamentação, pedido e provas condicionais. Os cenários completo e mínimo foram validados em navegador sem presumir documentos, cobrança indevida, negativação, restituição, danos, urgência, datas, valores ou providências não relatadas. A detecção de energia elétrica, cobrança indevida e negativação também passou a desconsiderar ocorrências presentes apenas após cláusulas de cautela como `sem inventar` ou `sem presumir`.

A área possui especialização transversal de endereçamento, qualificação, fundamentação, pedidos e provas nos escopos prioritários. As rotas bancárias prioritárias possuem validação combinada e isolada. Permanecem parciais os subtipos consumeristas ainda genéricos.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Veículo, contrato, retenção ou restituição do bem | ✅ | ✅ | ✅ | `v0.2.26`, `v0.2.36`, `v0.2.37`, `v0.2.38` | Validação real concluída; preservar danos e urgência somente quando expressamente relatados |
| Fraude bancária | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.39` | Validação real isolada concluída; preservar somente fatos, pedidos e provas efetivamente informados |
| Pix não reconhecido | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.39` | Validação real isolada concluída sem presumir cobrança, negativação ou documentos não relatados |
| Cobrança indevida | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.39` | Validação real isolada concluída; cobranças futuras e documentos permanecem condicionados ao relato |
| Negativação indevida | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.39` | Validação real isolada concluída; não presumir comunicação prévia, histórico ou efeitos concretos da restrição |
| Fraude + cobrança + negativação | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.39` | Cenário combinado e componentes isolados validados em navegador, com separação prudente dos escopos |
| Produto defeituoso | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.38` | Validação real concluída; preservar documentos, reparos e soluções compatíveis com a prova |
| Vício do produto | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.38` | Validação real concluída; aprofundar distinções jurídicas somente quando o caso exigir |
| Serviço defeituoso ou incompleto | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.38` | Validação real concluída; dano somente quando expressamente alegado e documentado |
| Serviço não prestado | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.40` | Validação real concluída nos cenários completo e mínimo; restituição somente quando houver pagamento informado |
| Plano de saúde e negativa de cobertura | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.38` | Validação real concluída; não inferir urgência, risco, exame, internação, cirurgia ou prontuário |
| Contrato consumerista geral | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.38`, `v0.2.41`, `v0.2.42`, `v0.2.43` | Fallback residual preservado para reembolso ou obrigação contratual adicional, sem duplicar oferta, publicidade, cancelamento ou entrega especializados |
| Oferta ou publicidade | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.41` | Validação real concluída nos cenários completo e mínimo; documentos e medidas somente quando efetivamente informados |
| Cancelamento não respeitado | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.42` | Validação real concluída nos cenários completo e mínimo; cobranças, pagamentos, restituição e documentos somente quando efetivamente informados |
| Atraso na entrega | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.43` | Validação real concluída nos cenários completo e mínimo; documentos, tentativas, entrega parcial, cancelamento, reembolso e danos somente quando efetivamente informados |
| Falha de garantia | ✅ | ✅ | ✅ | `v0.2.34`, `v0.2.36`, `v0.2.37`, `v0.2.38`, `v0.2.44` | Validação real concluída nos cenários completo e mínimo; documentos, reparos, soluções, danos e urgência somente quando efetivamente informados |
| Telefonia                                         |                       ✅ |                    ✅ |            ✅ | `v0.2.45`                                                                  | Validação real concluída nos cenários completo e mínimo; contrato, plano, faturas, protocolos, registros de falha, testes, suporte, portabilidade, danos e demais medidas somente quando efetivamente informados |
| Energia elétrica | ✅ | ✅ | ✅ | `v0.2.46` | Validação real concluída nos cenários completo e mínimo; unidade consumidora, faturas, protocolos, interrupção, medidor, vistoria, aviso de corte, religação, cobrança, negativação, danos e demais medidas somente quando efetivamente informados |
| Seguro | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar cobertura contratual própria |
| Turismo, companhia aérea ou hospedagem | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar pacote próprio |
| Superendividamento | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige fluxo próprio e cautelas específicas |
| Vazamento ou uso indevido de dados | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar pacote consumidor/LGPD |
| Marketplace e intermediação digital | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar definição de fornecedores e responsabilidades |

#### Próximo pacote recomendado

A `v0.2.46` concluiu a especialização e a validação real de energia elétrica, preservando as rotas genéricas de serviço defeituoso e serviço não prestado para os casos que não pertençam ao escopo específico de fornecimento de energia.

Próximos ciclos recomendados:

1. criar especialização consumerista própria para seguro;
2. preservar as regressões que impedem documentos, cobrança, negativação, restituição, danos, urgência, religação e outras medidas não informadas;
3. manter telefonia e energia elétrica isoladas das rotas genéricas incompatíveis.

---

### 7.4 Cível

#### Estado geral

Existe base geral e algumas rotas específicas.

O Cível puro ainda precisa de estrutura semelhante à criada em Família e Consumidor.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Cobrança contratual sem dano moral | ✅ | 🟡 | 🟡 | `v0.2.25` | Especializar provas, endereçamento e qualificação |
| Obrigação de fazer | ✅ | 🟡 | 🟡 | Rota `obligation_to_do_or_not_do` | Criar provas e testes dedicados |
| Obrigação de não fazer | ✅ | 🟡 | 🟡 | Rota `obligation_to_do_or_not_do` | Criar provas e testes dedicados |
| Indenização por dano material | ✅ | 🟡 | 🟡 | Rota `civil_damages_claim` | Especializar documentos e critérios de quantificação |
| Indenização por dano moral | ✅ | 🟡 | 🟡 | Rota `civil_damages_claim` | Evitar dano automático e criar testes próprios |
| Responsabilidade civil geral | ✅ | 🟡 | 🟡 | Base cível e fallback | Criar detecção por causa |
| Prestação de contas | 🟡 | 🟡 | 🟡 | Fallback prudente menciona prestação de contas | Criar ação própria |
| Exibição de documentos | 🟡 | 🟡 | 🟡 | Presente em rotas e fallback | Criar ação própria quando for pedido principal |
| Posse ou propriedade | 🟡 | 🔴 | 🔴 | Apenas referência histórica | Criar cobertura específica |
| Usucapião | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo documental e registral |
| Contratos complexos | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar análise contratual própria |
| Imobiliário | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar pacote próprio |
| Inventário e sucessões | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar área ou submódulo próprio |
| Produção antecipada de provas | 🔴 | 🔴 | 🔴 | Sem rota cível específica | Criar ciclo completo |
| Tutela antecedente ou cautelar autônoma | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige tratamento processual próprio |

#### Próximos pacotes recomendados

1. Completar cobrança contratual.
2. Completar obrigação de fazer ou não fazer.
3. Completar responsabilidade civil e danos.
4. Depois escolher um novo núcleo: possessório, imobiliário ou sucessões.

---

### 7.5 Previdenciário / BPC-LOAS

#### Estado geral

Existe módulo, checklist e fluxo QA para BPC/LOAS.

O Editor de sete blocos ainda não possui especialização previdenciária própria.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| BPC/LOAS da pessoa idosa | ✅ | 🔴 | 🟡 | Checklist e QA previdenciário | Criar Editor específico |
| BPC/LOAS da pessoa com deficiência | ✅ | 🔴 | 🟡 | Checklist e QA previdenciário | Criar Editor específico |
| Vulnerabilidade e composição familiar | ✅ | 🔴 | 🟡 | Checklist BPC/LOAS | Criar fundamentação e provas específicas |
| CadÚnico e renda familiar | ✅ | 🔴 | 🟡 | Checklist BPC/LOAS | Criar bloco probatório específico |
| Benefício por incapacidade temporária | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Aposentadoria por incapacidade permanente | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Aposentadoria por idade | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Aposentadoria por tempo de contribuição | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Revisão de benefício | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Restabelecimento de benefício | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Recurso administrativo | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar fluxo próprio |
| Cumprimento de exigência | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar fluxo documental próprio |
| Aposentadoria rural | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar módulo probatório próprio |
| Aposentadoria especial | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar integração com PPP/LTCAT previdenciário |
| Pensão por morte | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar módulo próprio |
| Salário-maternidade | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar módulo próprio |

#### Próximo pacote recomendado

Criar o primeiro Editor previdenciário com foco restrito em:

- BPC/LOAS;
- pessoa idosa;
- pessoa com deficiência;
- renda;
- composição familiar;
- CadÚnico;
- prova social;
- prova médica;
- requerimento e indeferimento administrativo.

Não misturar BPC/LOAS com benefícios contributivos.

---

### 7.6 Criminal

#### Estado geral

Existe pacote operacional inicial validado e hardenizado.

Essa validação não representa especialização atual do Editor de sete blocos.

| Tipo de medida ou ação | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| Liberdade provisória | ✅ | 🔴 | 🟡 | Pacote criminal inicial | Criar Editor específico |
| Habeas corpus inicial | ✅ | 🔴 | 🟡 | Pacote criminal inicial | Criar estrutura própria, sem forçar sete blocos cíveis |
| Relaxamento de prisão | ✅ | 🔴 | 🟡 | Pacote criminal inicial | Criar Editor específico |
| Resposta à acusação | ✅ | 🔴 | 🟡 | Pacote criminal inicial e hardening | Criar Editor específico |
| Revogação de prisão preventiva | ✅ | 🔴 | 🟡 | Checklist criminal | Criar especialização |
| Medidas cautelares diversas da prisão | ✅ | 🔴 | 🟡 | Checklist criminal | Criar especialização |
| Pedido de audiência de custódia | ✅ | 🔴 | 🟡 | Checklist criminal | Criar fluxo próprio |
| Pedido de diligência | ✅ | 🔴 | 🟡 | Checklist criminal | Criar fluxo próprio |
| Cadeia de custódia | 🟡 | 🔴 | 🔴 | Referência operacional | Criar módulo de prova específico |
| Tribunal do Júri | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Execução penal | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Recurso criminal | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Queixa-crime | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Medidas protetivas | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige tratamento sensível próprio |

#### Próxima regra

O Criminal não deve ser encaixado à força no mesmo formato das ações cíveis.

Antes de especializar, deve ser definido o contrato estrutural adequado para cada medida criminal.

---

### 7.7 Civil/Ambiental

#### Estado geral

Existe audiência estratégica, checklist e QA documentado.

O Editor atual ainda não possui roteador específico para Civil/Ambiental.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| Direito de vizinhança | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar Editor específico |
| Ruído excessivo | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar prova técnica e pedidos próprios |
| Poeira ou partículas | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar prova técnica e pedidos próprios |
| Vibração | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar prova técnica e pedidos próprios |
| Poluição ou dano ambiental local | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar Editor específico |
| Obrigação de cessar atividade nociva | ✅ | 🟡 | 🟡 | Rota cível geral de obrigação | Especializar nexo, urgência e prova técnica |
| Indenização material ambiental ou de vizinhança | ✅ | 🟡 | 🟡 | Rota cível geral de danos | Especializar nexo e quantificação |
| Indenização moral em contexto ambiental | ✅ | 🟡 | 🟡 | Rota cível geral de danos | Evitar presunção e especializar prova |
| Perícia ambiental, acústica ou de engenharia | ✅ | 🔴 | 🟡 | Checklist e QA | Criar bloco probatório específico |
| Produção antecipada de prova ambiental | ✅ | 🔴 | 🟡 | Checklist | Criar ação específica |
| Licenciamento ambiental | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo administrativo ambiental |
| Auto de infração ambiental | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo administrativo e sancionatório |
| Ação civil pública ambiental | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo coletivo próprio |

#### Próximo pacote recomendado

Criar pacote único de conflito de vizinhança e impacto local:

- ruído;
- poeira;
- vibração;
- atividade nociva;
- obrigação de fazer ou não fazer;
- tutela baseada em risco concreto;
- perícia;
- laudo;
- fiscalização;
- nexo causal.

---

### 7.8 Empresarial / Contratos / Cobrança

#### Estado geral

A área ainda não está formalmente consolidada como módulo completo.

Existe uma entrega específica de cobrança contratual no núcleo cível.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| Cobrança contratual simples sem dano moral | 🟡 | 🟡 | 🟡 | `v0.2.25` | Completar provas, partes e enquadramento |
| Prestação de serviço inadimplida | 🟡 | 🔴 | 🟡 | Planejamento antigo | Criar especialização |
| Rescisão contratual | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar especialização |
| Notificação extrajudicial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo documental próprio |
| Confissão de dívida | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo próprio |
| Acordo extrajudicial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo próprio |
| Ação monitória | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar especialização |
| Execução de título extrajudicial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar especialização |
| Análise de cláusulas | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar assistente contratual separado |
| Contrato de prestação de serviços | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo próprio |
| Dissolução societária | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo societário |
| Recuperação de crédito empresarial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo próprio |

#### Trava

Não criar um grande módulo empresarial genérico.

A evolução deve começar por um tipo de ação real, com documentos e resultado esperado claramente definidos.

---

## 8. Resumo executivo por área

| Área | Estado geral atual | Leitura correta |
|---|---:|---|
| Trabalhista | 🟡 Parcial avançado | Forte em risco laboral; horas e demais ações ainda incompletas |
| Família | ✅ Pronto no núcleo atual | Alimentos, guarda e convivência especializados e testados |
| Consumidor | 🟡 Parcial avançado | Sete blocos especializados; validação real concluída nos escopos prioritários, em serviço não prestado e nas rotas bancárias combinada e isoladas; subtipos ainda precisam expansão |
| Cível | 🟡 Parcial | Algumas rotas específicas, sem arquitetura completa por ação |
| Previdenciário | 🟡 Operacional, Editor pendente | BPC/LOAS possui base e QA, mas não Editor específico |
| Criminal | 🟡 Operacional, Editor pendente | Pacote inicial validado fora do Editor atual |
| Civil/Ambiental | 🟡 Operacional, Editor pendente | Checklist e QA existentes, sem roteador próprio |
| Empresarial/Contratos | 🔴 Inicial | Apenas cobrança contratual simples possui avanço parcial |

---

## 9. Ordem de prioridade recomendada

A prioridade deve considerar ganho jurídico, fechamento de lacunas existentes e risco de regressão.

### Prioridade 1 — completar áreas já roteadas

1. Provas específicas de horas extras e intervalo.
2. Provas, partes e endereçamento da cobrança contratual.

### Prioridade 2 — transformar módulos operacionais em Editor especializado

1. BPC/LOAS.
2. Criminal inicial, após definir estrutura adequada por medida.
3. Civil/Ambiental de vizinhança e impacto local.

### Prioridade 3 — ampliar Trabalhista

1. Acidente e doença ocupacional.
2. Vínculo, CTPS, verbas e FGTS.
3. Rescisão indireta.
4. Equiparação salarial.
5. Assédio.
6. Estabilidade.

### Prioridade 4 — ampliar Família

1. Revisão e exoneração de alimentos.
2. Divórcio e união estável.
3. Partilha.
4. Investigação de paternidade.
5. Curatela, tutela e adoção.

### Prioridade 5 — novas famílias consumeristas e cíveis

1. Seguro.
2. Turismo.
3. Superendividamento.
4. Dados pessoais e LGPD.
5. Possessório e imobiliário.
6. Sucessões.

---

## 10. Fluxo obrigatório de evolução

Toda nova especialização deverá seguir este ciclo:

1. escolher um item desta matriz;
2. definir o escopo exato;
3. criar ou selecionar caso real supervisionado;
4. executar o caso no navegador;
5. registrar as falhas concretas;
6. especializar somente o necessário;
7. criar testes unitários;
8. executar a regressão completa;
9. validar novamente no navegador;
10. abrir e revisar o pull request;
11. mergear;
12. criar tag oficial;
13. atualizar esta matriz.

Nenhuma etapa deve ser pulada.

---

## 11. Regra para alteração de status

### De 🔴 para 🟡

Exige pelo menos:

- escopo documentado;
- checklist ou contrato inicial;
- comportamento prudente identificável;
- alguma cobertura operacional ou implementação parcial;
- declaração explícita das limitações.

### De 🟡 para ✅

Exige:

- detecção específica;
- fundamentação específica;
- pedidos específicos;
- provas específicas;
- cautelas preservadas;
- testes dedicados;
- regressão completa;
- teste real no navegador;
- merge;
- tag;
- atualização desta matriz.

Nenhum status deve ser elevado apenas porque o texto parece bom visualmente.

---

## 12. Regras contra regressão

Toda nova entrega deve provar que:

- não misturou áreas jurídicas;
- não adicionou pedido incompatível;
- não inventou prova;
- não removeu cautelas;
- não alterou blocos não relacionados;
- não quebrou casos anteriores;
- não transformou fallback em especialização falsa;
- não tratou ausência de dados como autorização para completar fatos;
- não aumentou texto sem ganho jurídico real.

---

## 13. Relação com documentos anteriores

Os documentos anteriores continuam válidos como histórico e apoio operacional, especialmente:

- `docs/LEGAL_MODULES_V1.md`;
- `docs/LEGAL_MODULE_CHECKLISTS_V1.md`;
- `docs/LEGAL_MODULE_CHECKLISTS_V2.md`;
- `docs/LEGAL_MODULE_COVERAGE_MATRIX_V1.md`;
- relatórios QA por área.

Entretanto, este documento passa a ser a referência principal para:

- estado atual da cobertura;
- escolha das próximas especializações;
- classificação de pronto, parcial ou inexistente;
- atualização posterior a cada versão.

A matriz antiga em `docs/LEGAL_MODULE_COVERAGE_MATRIX_V1.md` não deve ser apagada, pois registra uma fase histórica baseada principalmente em cobertura operacional e Audiência Estratégica.

---

## 14. Registro de atualizações

| Data | Versão | Alteração |
|---|---|---|
| 2026-07-21 | `v0.2.35` | Criação da matriz oficial de cobertura jurídica após a `v0.2.34` |
| 2026-07-22 | `v0.2.36` | Especialização do Bloco 6 por escopo consumerista, com regressão e validação real de fraude Pix, cobrança e negativação |
| 2026-07-22 | `v0.2.37` | Especialização consumerista dos Blocos 1 e 2, com limites civis prudentes, preservação das partes e validação real no navegador |
| 2026-07-31 | `v0.2.42` | Especialização de cancelamento solicitado e não efetivado, com fundamentação, pedidos e provas condicionais e validação real dos cenários completo e mínimo |
| 2026-08-05 | `v0.2.43` | Especialização de atraso ou falha de entrega, com fundamentação, pedido e provas condicionais, isolamento do fallback contratual e validação real dos cenários completo e mínimo |
| 2026-08-05 | `v0.2.44` | Especialização de falha de garantia, com fundamentação, pedido e provas condicionais, isolamento da rota geral de produto defeituoso e validação real dos cenários completo e mínimo |
| 2026-08-10 | `v0.2.45` | Especialização de telefonia e telecomunicações, com fundamentação, pedido e provas condicionais, isolamento da rota geral de serviço defeituoso e validação real dos cenários completo e mínimo |
| 2026-08-10 | `v0.2.46` | Especialização de energia elétrica, com fundamentação, pedido e provas condicionais, isolamento das rotas genéricas de serviço defeituoso e serviço não prestado, proteção contra falsos escopos em cláusulas negativas e validação real dos cenários completo e mínimo |

A cada nova tag jurídica:

1. atualizar o item afetado;
2. registrar a versão;
3. explicar o que ficou pronto;
4. manter explícito o que continua pendente.

---

## 15. Diretriz final

O objetivo da Plataforma Jurídica Pro não é produzir o maior texto possível.

O objetivo é produzir a melhor primeira minuta possível, com:

- precisão;
- prudência;
- coerência;
- especialização;
- consistência entre fatos, fundamentos, pedidos e provas;
- ausência de informações inventadas;
- revisão profissional obrigatória;
- proteção automatizada contra regressões.

A matriz deve impedir que evolução técnica seja confundida com volume de funcionalidades.

Cobertura jurídica real é aquilo que foi delimitado, implementado, testado, validado e documentado.
